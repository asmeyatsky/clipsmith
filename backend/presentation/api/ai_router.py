import json
from fastapi import APIRouter, Depends, HTTPException, Request
from ...infrastructure.repositories.database import get_session
from ...infrastructure.repositories.models import (
    VideoProjectDB,
    AICaptionJobDB,
    AITemplateDB,
    AIVideoGenerationDB,
    AIVoiceOverDB,
)
from sqlmodel import Session, select
from datetime import datetime

router = APIRouter(prefix="/api/ai", tags=["ai_tools"])


# ==================== AI Caption Generation ====================


@router.post("/captions/generate")
async def generate_ai_captions(
    request: Request,
    session: Session = Depends(get_session),
    current_user: dict = None,
):
    """Request AI-generated captions for a video."""
    body = await request.json()
    project_id = body.get("project_id")
    video_asset_id = body.get("video_asset_id")
    language = body.get("language", "en")

    if not project_id or not video_asset_id:
        raise HTTPException(
            status_code=400, detail="project_id and video_asset_id required"
        )

    if current_user:
        project = session.get(VideoProjectDB, project_id)
        if not project or project.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

    job = AICaptionJobDB(
        project_id=project_id,
        user_id=current_user.get("id") if current_user else "anonymous",
        video_asset_id=video_asset_id,
        language=language,
        status="pending",
    )
    session.add(job)
    session.commit()

    return {
        "success": True,
        "job_id": job.id,
        "message": "Caption generation job started",
    }


@router.get("/captions/{job_id}")
async def get_caption_job(
    job_id: str,
    session: Session = Depends(get_session),
    current_user: dict = None,
):
    """Get caption generation job status."""
    job = session.get(AICaptionJobDB, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if current_user and job.user_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": job.id,
        "status": job.status,
        "language": job.language,
        "captions": json.loads(job.result) if job.result else None,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


# ==================== AI Templates ====================


@router.get("/templates")
async def list_ai_templates(
    category: str = None,
    style: str = None,
    is_premium: bool = None,
    limit: int = 20,
    offset: int = 0,
    session: Session = Depends(get_session),
):
    """List available AI templates."""
    query = select(AITemplateDB).where(AITemplateDB.is_public == True)

    if category:
        query = query.where(AITemplateDB.category == category)
    if style:
        query = query.where(AITemplateDB.style == style)
    if is_premium is not None:
        query = query.where(AITemplateDB.is_premium == is_premium)

    templates = session.exec(query.offset(offset).limit(limit)).all()

    return {
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "style": t.style,
                "thumbnail_url": t.thumbnail_url,
                "is_premium": t.is_premium,
                "price": t.price,
                "usage_count": t.usage_count,
                "tags": json.loads(t.tags) if t.tags else [],
            }
            for t in templates
        ]
    }


@router.get("/templates/{template_id}")
async def get_template(
    template_id: str,
    session: Session = Depends(get_session),
):
    """Get a specific template."""
    template = session.get(AITemplateDB, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "category": template.category,
        "style": template.style,
        "thumbnail_url": template.thumbnail_url,
        "project_data": json.loads(template.project_data),
        "is_premium": template.is_premium,
        "price": template.price,
        "usage_count": template.usage_count,
        "tags": json.loads(template.tags) if template.tags else [],
    }


@router.post("/templates")
async def create_ai_template(
    request: Request,
    session: Session = Depends(get_session),
    current_user: dict = None,
):
    """Create a new AI template."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    body = await request.json()
    template = AITemplateDB(
        name=body.get("name"),
        description=body.get("description"),
        category=body.get("category", "general"),
        style=body.get("style", "modern"),
        thumbnail_url=body.get("thumbnail_url"),
        project_data=json.dumps(body.get("project_data", {})),
        is_premium=body.get("is_premium", False),
        price=body.get("price", 0.0),
        creator_id=current_user["id"],
        is_public=body.get("is_public", True),
        tags=json.dumps(body.get("tags", [])),
    )
    session.add(template)
    session.commit()

    return {"success": True, "template_id": template.id}


@router.post("/templates/{template_id}/use")
async def use_template(
    template_id: str,
    request: Request,
    session: Session = Depends(get_session),
    current_user: dict = None,
):
    """Use a template to create a new project."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    template = session.get(AITemplateDB, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.is_premium and template.price > 0:
        raise HTTPException(
            status_code=402, detail="Premium template requires purchase"
        )

    body = await request.json()
    project_data = json.loads(template.project_data)

    new_project = VideoProjectDB(
        user_id=current_user["id"],
        title=body.get("title", f"{template.name} Project"),
        description=body.get("description"),
        status="draft",
    )
    session.add(new_project)

    template.usage_count += 1
    session.add(template)
    session.commit()

    return {
        "success": True,
        "project_id": new_project.id,
        "message": "Project created from template",
    }


# ==================== AI Video Generation ====================


@router.post("/video/generate")
async def generate_ai_video(
    request: Request,
    session: Session = Depends(get_session),
    current_user: dict = None,
):
    """Request AI video generation."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    body = await request.json()

    job = AIVideoGenerationDB(
        project_id=body.get("project_id"),
        user_id=current_user["id"],
        generation_type=body.get("generation_type", "text_to_video"),
        prompt=body.get("prompt"),
        negative_prompt=body.get("negative_prompt"),
        duration=body.get("duration", 5.0),
        model_version=body.get("model_version", "v1"),
        settings=json.dumps(body.get("settings", {})),
        status="pending",
    )
    session.add(job)
    session.commit()

    return {
        "success": True,
        "job_id": job.id,
        "message": "Video generation job started",
    }


@router.get("/video/{job_id}")
async def get_video_generation_job(
    job_id: str,
    session: Session = Depends(get_session),
    current_user: dict = None,
):
    """Get video generation job status."""
    job = session.get(AIVideoGenerationDB, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if current_user and job.user_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": job.id,
        "status": job.status,
        "generation_type": job.generation_type,
        "prompt": job.prompt,
        "result_url": job.result_url,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


# ==================== AI Voice Over ====================


@router.post("/voiceover/generate")
async def generate_ai_voiceover(
    request: Request,
    session: Session = Depends(get_session),
    current_user: dict = None,
):
    """Request AI voice-over generation."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    body = await request.json()

    job = AIVoiceOverDB(
        project_id=body.get("project_id"),
        user_id=current_user["id"],
        text=body.get("text"),
        voice_id=body.get("voice_id", "default"),
        language=body.get("language", "en"),
        speed=body.get("speed", 1.0),
        status="pending",
    )
    session.add(job)
    session.commit()

    return {
        "success": True,
        "job_id": job.id,
        "message": "Voice-over generation job started",
    }


@router.get("/voiceover/{job_id}")
async def get_voiceover_job(
    job_id: str,
    session: Session = Depends(get_session),
    current_user: dict = None,
):
    """Get voice-over generation job status."""
    job = session.get(AIVoiceOverDB, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if current_user and job.user_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": job.id,
        "status": job.status,
        "text": job.text,
        "voice_id": job.voice_id,
        "result_url": job.result_url,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


@router.get("/voices")
async def list_available_voices(
    language: str = None,
    session: Session = Depends(get_session),
):
    """List available AI voice options."""
    voices = [
        {
            "id": "default",
            "name": "Default Voice",
            "language": "en",
            "gender": "neutral",
        },
        {"id": "male_1", "name": "Deep Male", "language": "en", "gender": "male"},
        {"id": "female_1", "name": "Soft Female", "language": "en", "gender": "female"},
        {"id": "energetic", "name": "Energetic", "language": "en", "gender": "neutral"},
        {"id": "narrator", "name": "Narrator", "language": "en", "gender": "male"},
    ]

    if language:
        voices = [v for v in voices if v["language"] == language]

    return {"voices": voices}
