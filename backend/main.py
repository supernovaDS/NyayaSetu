from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from services.storage_service import init_db

load_dotenv()
init_db()

app = FastAPI(title="NyayaSetu API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

from routes.upload import router as upload_router
from routes.dashboard import router as dashboard_router
from routes.precedents import router as precedents_router
from routes.admin import router as admin_router
from routes.pdf import router as pdf_router
from routes.deadline import router as deadline_router
app.include_router(upload_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(precedents_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(pdf_router, prefix="/api")
app.include_router(deadline_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
