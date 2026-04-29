# In-memory settings store for the hackathon MVP
current_settings = {
    "model_id": "gemini-3-flash-preview"
}

def get_current_model() -> str:
    return current_settings["model_id"]

def set_current_model(model_id: str):
    current_settings["model_id"] = model_id
