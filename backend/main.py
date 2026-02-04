from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from .presentation.api.video_router import router as video_router
from .presentation.api.auth_router import router as auth_router
from .presentation.api.user_router import router as user_router
from .presentation.api.feed_router import router as feed_router
from .presentation.api.notification_router import router as notification_router
from .presentation.api.hashtag_router import router as hashtag_router
from .presentation.api.moderation_router import router as moderation_router
from .presentation.api.monitoring_router import router as monitoring_router
from .presentation.api.video_editor_router import router as video_editor_router
from .presentation.api.payment_router import router as payment_router
from .presentation.api.analytics_router import router as analytics_router
from .presentation.middleware.monitoring_middleware import (
    MonitoringMiddleware,
    HealthCheckMiddleware,
    UserActivityMiddleware,
)
from .infrastructure.repositories.database import create_db_and_tables
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="clipsmith API", lifespan=lifespan)

# Add monitoring middleware
app.add_middleware(MonitoringMiddleware)
app.add_middleware(HealthCheckMiddleware)
app.add_middleware(UserActivityMiddleware)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS configuration - use environment variable for production
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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
app.include_router(feed_router)
app.include_router(notification_router)
app.include_router(hashtag_router)
app.include_router(moderation_router)
app.include_router(video_editor_router)
app.include_router(payment_router)
app.include_router(analytics_router)


@app.get("/")
async def root():
    return {"message": "Welcome to clipsmith API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
