import os
import json
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

EXTRACTION_PROMPT = """You are a legal document analysis AI for Indian government court cases.
Analyze the provided court judgment page images and extract structured data.
Be precise. If a field cannot be determined, use an empty string or empty array.

Return a JSON object with exactly two top-level keys: "extracted_data" and "action_plan".

"extracted_data" must contain:
- case_title (string): Full title of the case
- case_number (string): Case/writ number
- date_of_order (string): Date of court order, format YYYY-MM-DD
- state_role (string): "Petitioner" or "Respondent" — the role of the State/Government
- parties (array of strings): All parties involved
- directives (array of strings): Key orders/directives from the judgment
- timelines (array of strings): Any deadlines or time periods mentioned
- confidence (number 0.0-1.0): Your confidence in extraction accuracy

"action_plan" must contain:
- action_type (string): One of "compliance", "appeal", or "review"
- assigned_designation (string): Government authority responsible (e.g., "Secretary, Revenue Department")
- calculated_deadline (string): Deadline date based on order date + limitation period, format YYYY-MM-DD
- reasoning (string): Why this action is recommended
- contempt_risk_level (string): One of "critical", "high", "medium", "low"
- draft_file_note (string): A formal government file note. Start with "Reference is made to the judgment dated..."

Also include a third top-level key named "source_evidence".
"source_evidence" must be an object where each important field maps to:
- page (number): 1-indexed page number where the value appears
- quote (string): exact short source quote from the judgment, under 350 characters
- confidence (number 0.0-1.0): confidence that the quote supports the field

Use keys such as case_title, case_number, date_of_order, directives, timelines, and action_plan.
"""


async def extract_from_images(images: list[bytes], page_numbers: list[int]) -> dict | None:
    """Pass 2: Send critical page images to Gemini vision for structured extraction."""
    from services.settings_service import get_current_model
    model_id = get_current_model()

    parts = [types.Part.from_text(text=EXTRACTION_PROMPT)]

    for i, img_bytes in enumerate(images):
        parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))
        parts.append(types.Part.from_text(
            text=f"(This is page {page_numbers[i] + 1} of the judgment)"
        ))

    response = await client.aio.models.generate_content(
        model=model_id,
        contents=types.Content(role="user", parts=parts),
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
        ),
    )

    try:
        return json.loads(response.text)
    except (json.JSONDecodeError, TypeError):
        return None
