import os
import json
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PAGE_FINDER_PROMPT = """You are analyzing a court judgment document with {total_pages} pages.
The text below has page markers like "--- PAGE X ---".

Identify which pages contain:
1. Case metadata (case number, date, parties) — usually first 2-3 pages
2. Final orders, directives, or compliance requirements — usually last few pages
3. Any explicit deadlines or limitation periods

Return ONLY a JSON array of page numbers (1-indexed). Example: [1, 2, 45, 46, 47]
Do not include pages that only contain arguments or witness statements.

Document text:
{text}"""


async def find_critical_pages(full_text: str, total_pages: int) -> list[int]:
    """Pass 1: Ask Gemini which pages contain orders, directives, deadlines."""
    from services.settings_service import get_current_model
    model_id = get_current_model()

    # Truncate to avoid token limits — first 50k chars is enough for page identification
    prompt = PAGE_FINDER_PROMPT.format(
        total_pages=total_pages,
        text=full_text[:50000],
    )

    response = await client.aio.models.generate_content(
        model=model_id,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
        ),
    )

    try:
        pages = json.loads(response.text)
        # Convert to 0-indexed
        return [p - 1 for p in pages if isinstance(p, int) and 1 <= p <= total_pages]
    except (json.JSONDecodeError, TypeError):
        from services.pdf_service import get_fallback_pages
        return get_fallback_pages(total_pages)
