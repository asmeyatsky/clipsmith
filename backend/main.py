from fastapi import FastAPI
from contextlib import asynccontextmanager
from .presentation.api.video_router import router as video_router
from .presentation.api.auth_router import router as auth_router
from .presentation.api.user_router import router as user_router
from .infrastructure.repositories.database import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

from fastapi.staticfiles import StaticFiles
import os

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="clipsmith API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development convenience. In prod, specify domain.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads dir if not exists (redundant with adapter but safe)
os.makedirs("backend/uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="backend/uploads"), name="uploads")

app.include_router(auth_router)
app.include_router(video_router)
app.include_router(user_router)

@app.get("/")
async def root():
    return {"message": "Welcome to clipsmith API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "ok"}
