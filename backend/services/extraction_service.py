"""Orchestrates the two-pass extraction pipeline."""

from services.pdf_service import extract_text_with_pages, render_pages_as_images, get_fallback_pages, extract_page_texts, find_text_bbox
from services.llm_service import find_critical_pages
from services.vision_service import extract_from_images
from services.department_service import route_department
from services.quality_service import build_review_meta
from models.schemas import ExtractionResult, ExtractedData, ActionPlan, SourceEvidence


def _clip(text: str, limit: int = 350) -> str:
    text = " ".join(text.split())
    return text[:limit].strip()


def _find_quote(page_texts: list[str], needles: list[str], preferred_pages: list[int]) -> SourceEvidence:
    search_pages = preferred_pages or list(range(len(page_texts)))
    for needle in needles:
        cleaned = " ".join((needle or "").split())
        if len(cleaned) < 6:
            continue
        for page_idx in search_pages:
            if not (0 <= page_idx < len(page_texts)):
                continue
            normalized = " ".join(page_texts[page_idx].split())
            pos = normalized.lower().find(cleaned[:90].lower())
            if pos >= 0:
                start = max(0, pos - 90)
                end = min(len(normalized), pos + len(cleaned) + 180)
                return SourceEvidence(page=page_idx + 1, quote=_clip(normalized[start:end]), confidence=0.8)

    for page_idx in search_pages:
        if 0 <= page_idx < len(page_texts) and page_texts[page_idx].strip():
            return SourceEvidence(page=page_idx + 1, quote=_clip(page_texts[page_idx]), confidence=0.45)

    return SourceEvidence()


def _with_bbox(pdf_path: str, key: str, evidence: SourceEvidence, extracted: ExtractedData, action: ActionPlan) -> SourceEvidence:
    if evidence.bbox or evidence.page <= 0:
        return evidence

    candidates_by_key = {
        "case_title": [extracted.case_title, evidence.quote],
        "case_number": [extracted.case_number, evidence.quote],
        "date_of_order": [extracted.date_of_order, evidence.quote],
        "directives": [*(extracted.directives or []), evidence.quote],
        "timelines": [*(extracted.timelines or []), evidence.quote],
        "action_plan": [action.reasoning, action.draft_file_note, evidence.quote],
    }
    evidence.bbox = find_text_bbox(pdf_path, evidence.page, candidates_by_key.get(key, [evidence.quote]))
    return evidence


def _build_source_evidence(
    pdf_path: str,
    raw_evidence: dict,
    extracted: ExtractedData,
    action: ActionPlan,
    page_texts: list[str],
    critical_pages: list[int],
) -> dict[str, SourceEvidence]:
    evidence: dict[str, SourceEvidence] = {}

    if isinstance(raw_evidence, dict):
        for key, value in raw_evidence.items():
            if isinstance(value, dict):
                try:
                    evidence[key] = SourceEvidence(**value)
                except Exception:
                    continue

    first_pages = critical_pages[:2]
    directive_pages = critical_pages[-3:]
    fallback_map = {
        "case_title": ([extracted.case_title], first_pages),
        "case_number": ([extracted.case_number], first_pages),
        "date_of_order": ([extracted.date_of_order], first_pages),
        "directives": (extracted.directives, directive_pages),
        "timelines": (extracted.timelines, directive_pages),
        "action_plan": ([action.reasoning, action.draft_file_note], directive_pages),
    }

    for key, (needles, pages) in fallback_map.items():
        if key not in evidence or not evidence[key].quote:
            evidence[key] = _find_quote(page_texts, needles, pages)
        evidence[key] = _with_bbox(pdf_path, key, evidence[key], extracted, action)

    return evidence


async def process_judgment(pdf_path: str) -> ExtractionResult:
    """Full two-pass extraction pipeline for a court judgment PDF."""

    # Pass 1: Extract text and find critical pages
    full_text, total_pages = extract_text_with_pages(pdf_path)

    if len(full_text.strip()) < 500:
        # Scanned PDF with minimal extractable text — use heuristic fallback
        critical_pages = get_fallback_pages(total_pages)
    else:
        critical_pages = await find_critical_pages(full_text, total_pages)

    if not critical_pages:
        critical_pages = get_fallback_pages(total_pages)

    # Pass 2: Render critical pages as images, extract via vision
    images = render_pages_as_images(pdf_path, critical_pages)
    raw_result = await extract_from_images(images, critical_pages)

    if raw_result is None:
        raise ValueError("Gemini returned unparseable response. Manual entry required.")

    # Validate with Pydantic
    extracted = ExtractedData(**raw_result.get("extracted_data", {}))
    action = ActionPlan(**raw_result.get("action_plan", {}))

    routing = route_department(extracted.directives, extracted.parties)
    if not action.assigned_designation:
        action.assigned_designation = routing["department"]
    elif action.assigned_designation.lower() in {"not assigned", "unknown", "n/a"}:
        action.assigned_designation = routing["department"]
    if routing["reason"] not in action.reasoning:
        action.reasoning = f"{action.reasoning}\n\nRouting assist: {routing['reason']}".strip()

    # Override LLM-guessed deadlines with deterministic Limitation Act math
    from services.deadline_service import calculate_deadlines
    deadline_info = calculate_deadlines(extracted.date_of_order, action.action_type.value)
    action.calculated_deadline = deadline_info["calculated_deadline"]
    action.days_remaining = deadline_info["days_remaining"]
    action.contempt_risk_level = deadline_info["contempt_risk_level"]
    action.deadline_rule_id = deadline_info["deadline_rule_id"]
    action.deadline_basis = deadline_info["deadline_basis"]

    # Page references (simplified: first critical page = metadata, last = directives)
    page_refs = {}
    if critical_pages:
        page_refs["metadata"] = critical_pages[0] + 1
        page_refs["directives"] = critical_pages[-1] + 1

    page_texts = extract_page_texts(pdf_path)
    source_evidence = _build_source_evidence(
        pdf_path,
        raw_result.get("source_evidence", {}),
        extracted,
        action,
        page_texts,
        critical_pages,
    )
    review_meta = build_review_meta(extracted, action, source_evidence, total_pages, critical_pages)

    return ExtractionResult(
        extracted_data=extracted,
        action_plan=action,
        critical_pages=[p + 1 for p in critical_pages],  # 1-indexed for display
        page_references=page_refs,
        source_evidence=source_evidence,
        review_meta=review_meta,
    )
