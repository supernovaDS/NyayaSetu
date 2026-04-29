import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.extraction_service import process_judgment
from services.storage_service import add_audit_event

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_and_extract(file: UploadFile = File(...)):
    """Upload a court judgment PDF and run the two-pass extraction pipeline."""

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Save uploaded file
    job_id = str(uuid.uuid4())
    pdf_path = os.path.join(UPLOAD_DIR, f"{job_id}.pdf")

    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        result = await process_judgment(pdf_path)
        add_audit_event(
            job_id,
            "uploaded_and_extracted",
            "System",
            {"filename": file.filename, "critical_pages": result.critical_pages},
        )
        return {"job_id": job_id, **result.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
