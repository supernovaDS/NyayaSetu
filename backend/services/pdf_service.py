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


def find_text_bbox(pdf_path: str, page_number: int, candidates: list[str]) -> list[float]:
    """Find a normalized bounding box for candidate text on a 1-indexed page."""
    doc = fitz.open(pdf_path)
    try:
        if page_number <= 0 or page_number > len(doc):
            return []

        page = doc[page_number - 1]
        page_rect = page.rect
        search_terms = []
        for candidate in candidates:
            cleaned = " ".join((candidate or "").split())
            if len(cleaned) < 4:
                continue
            search_terms.extend([
                cleaned,
                cleaned[:140],
                cleaned[:90],
                cleaned[:60],
            ])

        for term in search_terms:
            if len(term) < 4:
                continue
            rects = page.search_for(term, quads=False)
            if rects:
                rect = rects[0]
                return [
                    max(0.0, rect.x0 / page_rect.width),
                    max(0.0, rect.y0 / page_rect.height),
                    min(1.0, rect.x1 / page_rect.width),
                    min(1.0, rect.y1 / page_rect.height),
                ]
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
