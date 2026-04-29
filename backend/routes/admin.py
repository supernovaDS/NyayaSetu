from fastapi import APIRouter
from pydantic import BaseModel
from services.settings_service import current_settings, set_current_model

router = APIRouter()

AVAILABLE_MODELS = [
    {"id": "gemini-3-flash-preview", "name": "Gemini 3 Flash"},
    {"id": "gemma-4-31b-it", "name": "Gemma 4 31B"},
    {"id": "gemini-3.1-flash-lite-preview", "name": "Gemini 3.1 Flash Lite"},
]

class ModelUpdate(BaseModel):
    model_id: str

@router.get("/config")
def get_config():
    return {
        "current_model": current_settings["model_id"],
        "available_models": AVAILABLE_MODELS
    }

@router.post("/config")
def update_config(update: ModelUpdate):
    set_current_model(update.model_id)
    return {"status": "success", "current_model": current_settings["model_id"]}
