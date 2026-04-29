from fastapi import APIRouter
from services.precedent_service import search_precedents

router = APIRouter()


@router.get("/precedents")
async def get_precedents(query: str):
    results = await search_precedents(query)
    return {"precedents": results}
