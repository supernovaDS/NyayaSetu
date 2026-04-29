import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from services.pdf_service import render_page_as_png

router = APIRouter()


@router.get("/pdf/{job_id}/page/{page_number}")
async def get_pdf_page(job_id: str, page_number: int):
    pdf_path = os.path.join("uploads", f"{job_id}.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    try:
        image = render_page_as_png(pdf_path, page_number)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not render page: {exc}") from exc
    return Response(content=image, media_type="image/png")
