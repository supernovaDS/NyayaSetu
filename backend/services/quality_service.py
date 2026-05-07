"""Decision-readiness scoring and triage flags for extracted judgments."""

from models.schemas import ActionPlan, ExtractedData, ReviewFlag, ReviewMeta, SourceEvidence


CATEGORY_RULES = [
    ("Service Matter", ("promotion", "seniority", "appointment", "reinstatement", "termination", "pay scale", "employee")),
    ("Land Acquisition", ("land acquisition", "compensation", "acquired land", "award", "possession")),
    ("Pension / Retirement", ("pension", "gratuity", "retirement", "arrears")),
    ("Infrastructure / Contract", ("contract", "tender", "highway", "road", "bridge", "contractor", "works")),
    ("Environment", ("pollution", "environment", "forest", "clearance", "industrial unit")),
    ("Education", ("school", "teacher", "student", "university", "education")),
    ("Home / Police", ("police", "fir", "investigation", "law and order")),
]


def classify_case(extracted: ExtractedData) -> str:
    text = " ".join([
        extracted.case_title,
        " ".join(extracted.parties),
        " ".join(extracted.directives),
    ]).lower()

    for category, keywords in CATEGORY_RULES:
        if any(keyword in text for keyword in keywords):
            return category
    return "General Administrative"


def _impact_summary(category: str, action_type: str) -> str:
    impacts = {
        "Service Matter": "Directly affects employee service rights, pay, seniority, or reinstatement, so delay can create avoidable arrears and contempt exposure.",
        "Land Acquisition": "Likely affects compensation or possession decisions, so timely action can reduce citizen hardship and interest liability.",
        "Pension / Retirement": "Affects retirement benefits and livelihood security, making delay especially visible and sensitive.",
        "Infrastructure / Contract": "Can affect public works delivery, contractor payments, and departmental financial exposure.",
        "Environment": "May affect regulatory compliance and public health obligations.",
        "Education": "Can affect students, teachers, institutions, or admission/service decisions.",
        "Home / Police": "May require sensitive coordination with police or home authorities where delay can affect public trust.",
    }
    base = impacts.get(category, "Requires administrative decision-making backed by a verified legal record.")
    return f"{base} Recommended primary response: {action_type}."


def build_review_meta(
    extracted: ExtractedData,
    action: ActionPlan,
    source_evidence: dict[str, SourceEvidence],
    total_pages: int,
    critical_pages: list[int],
) -> ReviewMeta:
    flags: list[ReviewFlag] = []
    score = 100

    required_fields = {
        "case number": extracted.case_number,
        "date of order": extracted.date_of_order,
        "directives": extracted.directives,
        "responsible office": action.assigned_designation,
        "deadline": action.calculated_deadline,
    }
    for label, value in required_fields.items():
        missing = not value if not isinstance(value, list) else len(value) == 0
        if missing:
            score -= 14
            flags.append(ReviewFlag(
                severity="critical" if label in {"date of order", "directives"} else "warning",
                title=f"Missing {label}",
                detail=f"The {label} could not be confidently prepared and must be verified manually.",
            ))

    if extracted.confidence < 0.45:
        score -= 20
        flags.append(ReviewFlag(
            severity="critical",
            title="Low extraction confidence",
            detail="The model reported low confidence; reviewer should compare every field against the source PDF.",
        ))
    elif extracted.confidence < 0.7:
        score -= 8
        flags.append(ReviewFlag(
            severity="warning",
            title="Moderate extraction confidence",
            detail="Some extracted fields may need closer manual verification.",
        ))

    evidence_keys = ["case_number", "date_of_order", "directives"]
    missing_evidence = [key for key in evidence_keys if not source_evidence.get(key, SourceEvidence()).quote]
    if missing_evidence:
        score -= 10
        flags.append(ReviewFlag(
            severity="warning",
            title="Evidence gaps",
            detail=f"Missing source quotes for: {', '.join(missing_evidence)}.",
        ))

    bbox_count = sum(1 for item in source_evidence.values() if item.bbox)
    if source_evidence and bbox_count == 0:
        score -= 6
        flags.append(ReviewFlag(
            severity="info",
            title="Page-level evidence only",
            detail="Source quotes are available, but exact text coordinates were not found for highlighting.",
        ))

    if action.days_remaining >= 0 and action.days_remaining <= 7:
        flags.append(ReviewFlag(
            severity="critical",
            title="Deadline is near",
            detail=f"Only {action.days_remaining} days remain. Escalate after verification.",
        ))

    pages_reduced = max(total_pages - len(set(critical_pages)), 0)
    estimated_minutes_saved = max(pages_reduced * 2, 0)
    evidence_keys = ["case_title", "case_number", "date_of_order", "directives", "timelines", "action_plan"]
    covered = sum(1 for key in evidence_keys if source_evidence.get(key, SourceEvidence()).quote)
    source_coverage = round((covered / len(evidence_keys)) * 100)

    if extracted.confidence >= 0.8 and source_coverage >= 70:
        confidence_label = "evidence-backed"
    elif extracted.confidence >= 0.6:
        confidence_label = "review-ready"
    else:
        confidence_label = "manual-check"

    if action.service_level:
        triage_lane = action.service_level
    elif action.contempt_risk_level in {"critical", "high"}:
        triage_lane = "red_lane"
    else:
        triage_lane = "standard"

    case_category = classify_case(extracted)
    return ReviewMeta(
        case_category=case_category,
        readiness_score=max(0, min(100, score)),
        flags=flags,
        estimated_minutes_saved=estimated_minutes_saved,
        pages_reduced=pages_reduced,
        critical_pages_count=len(set(critical_pages)),
        impact_summary=_impact_summary(case_category, action.action_type.value),
        triage_lane=triage_lane,
        source_coverage=source_coverage,
        confidence_label=confidence_label,
    )
