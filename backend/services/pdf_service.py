import re
from difflib import SequenceMatcher

import fitz  # PyMuPDF


def extract_text_with_pages(pdf_path: str) -> tuple[str, int]:
    """Extract raw text from all pages with page markers. Returns (full_text, total_pages)."""
    doc = fitz.open(pdf_path)
    total = len(doc)

    parts = []
    for page in doc:
        parts.append(f"\n--- PAGE {page.number + 1} ---\n")
        parts.append(page.get_text())

    doc.close()
    return "".join(parts), total


def extract_page_texts(pdf_path: str) -> list[str]:
    """Return raw text for every page, preserving page order."""
    doc = fitz.open(pdf_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return pages


def render_pages_as_images(pdf_path: str, page_numbers: list[int]) -> list[bytes]:
    """Convert specific PDF pages to PNG images at 2x zoom."""
    doc = fitz.open(pdf_path)
    images = []

    for pg_num in page_numbers:
        if 0 <= pg_num < len(doc):
            pix = doc[pg_num].get_pixmap(matrix=fitz.Matrix(2, 2))
            images.append(pix.tobytes("png"))

    doc.close()
    return images


def render_page_as_png(pdf_path: str, page_number: int, zoom: float = 1.6) -> bytes:
    """Render a single 1-indexed PDF page as PNG bytes."""
    doc = fitz.open(pdf_path)
    try:
        page_index = max(0, min(page_number - 1, len(doc) - 1))
        pix = doc[page_index].get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        return pix.tobytes("png")
    finally:
        doc.close()


def get_page_count(pdf_path: str) -> int:
    """Return total pages in a PDF."""
    doc = fitz.open(pdf_path)
    try:
        return len(doc)
    finally:
        doc.close()


def _normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _candidate_texts(candidates: list[str]) -> list[str]:
    seen = set()
    texts = []
    for candidate in candidates:
        cleaned = " ".join((candidate or "").split())
        if len(cleaned) < 8:
            continue
        variants = [cleaned]
        if len(cleaned) > 180:
            variants.extend([cleaned[:180], cleaned[:130], cleaned[:90]])
        elif len(cleaned) > 90:
            variants.extend([cleaned[:130], cleaned[:90]])
        for variant in variants:
            key = variant.lower()
            if key not in seen and len(variant) >= 8:
                seen.add(key)
                texts.append(variant)
    return texts


def _rect_to_normalized(rect: fitz.Rect, page_rect: fitz.Rect) -> list[float]:
    return [
        max(0.0, rect.x0 / page_rect.width),
        max(0.0, rect.y0 / page_rect.height),
        min(1.0, rect.x1 / page_rect.width),
        min(1.0, rect.y1 / page_rect.height),
    ]


def _word_level_bbox(page: fitz.Page, candidates: list[str]) -> list[float]:
    words = page.get_text("words")
    if not words:
        return []

    words = sorted(words, key=lambda item: (item[5], item[6], item[7], item[1], item[0]))
    normalized_words = [_normalize_token(item[4]) for item in words]
    page_rect = page.rect
    best_score = 0.0
    best_span: tuple[int, int] | None = None

    for candidate in _candidate_texts(candidates):
        target_tokens = [_normalize_token(token) for token in candidate.split()]
        target_tokens = [token for token in target_tokens if token]
        if len(target_tokens) < 2:
            continue

        target = " ".join(target_tokens[:45])
        target_len = min(len(target_tokens), 45)
        window_sizes = sorted({target_len, max(2, target_len - 3), min(len(words), target_len + 3)})

        for size in window_sizes:
            if size > len(words):
                continue
            for start in range(0, len(words) - size + 1):
                window_tokens = [token for token in normalized_words[start:start + size] if token]
                if len(window_tokens) < 2:
                    continue
                window = " ".join(window_tokens)
                overlap = len(set(window_tokens) & set(target_tokens)) / max(len(set(target_tokens)), 1)
                ratio = SequenceMatcher(None, window, target).ratio()
                first_token_bonus = 0.08 if target_tokens[0] in window_tokens[:3] else 0
                score = (ratio * 0.68) + (overlap * 0.32) + first_token_bonus
                if score > best_score:
                    best_score = score
                    best_span = (start, start + size)

    if not best_span or best_score < 0.72:
        return []

    rects = [fitz.Rect(*word[:4]) for word in words[best_span[0]:best_span[1]]]
    union = rects[0]
    for rect in rects[1:]:
        union |= rect

    padding_x = page_rect.width * 0.004
    padding_y = page_rect.height * 0.003
    union.x0 = max(page_rect.x0, union.x0 - padding_x)
    union.x1 = min(page_rect.x1, union.x1 + padding_x)
    union.y0 = max(page_rect.y0, union.y0 - padding_y)
    union.y1 = min(page_rect.y1, union.y1 + padding_y)
    return _rect_to_normalized(union, page_rect)


def find_text_bbox(pdf_path: str, page_number: int, candidates: list[str]) -> list[float]:
    """Find a normalized bounding box for candidate text on a 1-indexed page."""
    doc = fitz.open(pdf_path)
    try:
        if page_number <= 0 or page_number > len(doc):
            return []

        page = doc[page_number - 1]
        page_rect = page.rect
        search_terms = _candidate_texts(candidates)

        for term in search_terms:
            if len(term) < 4:
                continue
            rects = page.search_for(term, quads=False)
            if rects:
                union = rects[0]
                for rect in rects[1:]:
                    union |= rect
                return _rect_to_normalized(union, page_rect)

        return _word_level_bbox(page, candidates)
    finally:
        doc.close()

    return []


def get_fallback_pages(total_pages: int) -> list[int]:
    """First 3 + Last 5 pages as fallback for scanned PDFs."""
    if total_pages <= 12:
        return list(range(total_pages))

    first = list(range(min(3, total_pages)))
    last = list(range(max(0, total_pages - 5), total_pages))
    return sorted(set(first + last))
