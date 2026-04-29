from fastapi import APIRouter
from pydantic import BaseModel
from services.deadline_service import calculate_deadlines, list_deadline_rules

router = APIRouter()


class DeadlineRequest(BaseModel):
    date_of_order: str
    action_type: str
    override_days: int | None = None


@router.get("/deadline-rules")
async def get_deadline_rules():
    return {"rules": list_deadline_rules()}


@router.post("/deadline-rules/calculate")
async def calculate_deadline(req: DeadlineRequest):
    return calculate_deadlines(req.date_of_order, req.action_type, req.override_days)
