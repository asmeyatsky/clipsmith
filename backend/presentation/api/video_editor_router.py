import json
import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated, List, Optional
from ...application.services.video_editor_service import VideoEditorService
from ...infrastructure.repositories.sqlite_video_editor_repo import (
    SQLiteVideoEditorRepository,
)
from ...infrastructure.repositories.database import get_session
from ...infrastructure.security.jwt_adapter import JWTAdapter
from sqlmodel import Session, select
from ...infrastructure.repositories.models import (
    VideoProjectDB,
    VideoEditorKeyframeDB,
    VideoEditorColorGradeDB,
    VideoEditorAudioMixDB,
    VideoEditorChromaKeyDB,
    VideoEditorEffectDB,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    request: Request,
):
    token = request.cookies.get("access_token")
    if not token:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    payload = JWTAdapter.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
        )
    return {"id": payload.get("user_id"), "email": payload.get("sub")}


router = APIRouter(prefix="/api/editor", tags=["video_editor"])


def get_video_editor_service(
    session: Session = Depends(get_session),
) -> VideoEditorService:
    """Dependency injection for video editor service."""
    repository = SQLiteVideoEditorRepository(session)
    return VideoEditorService(repository)


# Project endpoints
@router.post("/projects")
async def create_project(
    title: str = Form("Untitled Project"),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Create a new video project."""
    project = service.create_project(
        user_id=current_user["id"], title=title, description=description
    )
    return {"success": True, "project": project}


@router.get("/projects")
async def get_user_projects(
    status: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Get user's video projects."""
    from ...domain.entities.video_editor import VideoProjectStatus

    project_status = VideoProjectStatus(status) if status else None
    projects = service.get_user_projects(
        user_id=current_user["id"], limit=limit, status=project_status
    )
    return {"success": True, "projects": projects}


@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Get a specific project."""
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return {"success": True, "project": project}


@router.put("/projects/{project_id}/title")
async def update_project_title(
    project_id: str,
    title: str = Form(...),
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Update project title."""
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    updated_project = service.update_project_title(project_id, title)
    return {"success": True, "project": updated_project}


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Delete a project."""
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    success = service.delete_project(project_id)
    return {"success": success}


# Asset endpoints
@router.post("/projects/{project_id}/assets")
async def upload_asset(
    project_id: str,
    file: UploadFile = File(...),
    asset_type: str = Form(...),
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Upload an asset to a project."""
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Here you would typically upload the file to cloud storage
    # For now, we'll simulate with a URL

    file_content = await file.read()
    file_size = len(file_content)

    # Save file locally for now (in production, use cloud storage)
    upload_dir = "backend/uploads/editor"
    os.makedirs(upload_dir, exist_ok=True)

    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)

    with open(file_path, "wb") as f:
        f.write(file_content)

    asset_url = f"/uploads/editor/{unique_filename}"

    asset = service.upload_asset(
        project_id=project_id,
        asset_type=asset_type,
        filename=file.filename,
        file_size=file_size,
        mime_type=file.content_type,
        url=asset_url,
    )

    return {"success": True, "asset": asset}


@router.get("/projects/{project_id}/assets")
async def get_project_assets(
    project_id: str,
    asset_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Get assets for a project."""
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    assets = service.get_project_assets(project_id, asset_type)
    return {"success": True, "assets": assets}


@router.delete("/assets/{asset_id}")
async def delete_asset(
    asset_id: str,
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Delete an asset."""
    asset = service.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    project = service.get_project(asset.project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    success = service.delete_asset(asset_id)
    return {"success": success}


# Transition endpoints
@router.post("/projects/{project_id}/transitions")
async def add_transition(
    project_id: str,
    transition_type: str = Form(...),
    start_time: float = Form(...),
    end_time: float = Form(...),
    duration: float = Form(...),
    parameters: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Add a transition to a project."""
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    transition_params = json.loads(parameters) if parameters else None

    transition = service.add_transition(
        project_id=project_id,
        transition_type=transition_type,
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        parameters=transition_params,
    )

    return {"success": True, "transition": transition}


@router.get("/projects/{project_id}/transitions")
async def get_project_transitions(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Get transitions for a project."""
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    transitions = service.get_project_transitions(project_id)
    return {"success": True, "transitions": transitions}


# Track endpoints
@router.post("/projects/{project_id}/tracks")
async def add_track(
    project_id: str,
    asset_id: str = Form(...),
    track_type: str = Form(...),
    start_time: float = Form(...),
    end_time: float = Form(...),
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Add a track to a project."""
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    track = service.add_track(
        project_id=project_id,
        asset_id=asset_id,
        track_type=track_type,
        start_time=start_time,
        end_time=end_time,
    )

    return {"success": True, "track": track}


@router.get("/projects/{project_id}/tracks")
async def get_project_tracks(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Get tracks for a project."""
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    tracks = service.get_project_tracks(project_id)
    return {"success": True, "tracks": tracks}


# Caption endpoints
@router.post("/projects/{project_id}/captions")
async def add_caption(
    project_id: str,
    video_asset_id: str = Form(...),
    text: str = Form(...),
    start_time: float = Form(...),
    end_time: float = Form(...),
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Add a caption to a video."""
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    caption = service.add_caption(
        project_id=project_id,
        video_asset_id=video_asset_id,
        text=text,
        start_time=start_time,
        end_time=end_time,
    )

    return {"success": True, "caption": caption}


@router.get("/projects/{project_id}/videos/{video_asset_id}/captions")
async def get_project_captions(
    project_id: str,
    video_asset_id: str,
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Get captions for a video in a project."""
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    captions = service.get_project_captions(project_id, video_asset_id)
    return {"success": True, "captions": captions}


@router.delete("/captions/{caption_id}")
async def delete_caption(
    caption_id: str,
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Delete a caption."""
    caption = service.get_caption(caption_id)
    if not caption:
        raise HTTPException(status_code=404, detail="Caption not found")

    project = service.get_project(caption.project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    success = service.delete_caption(caption_id)
    return {"success": success}


@router.get("/projects/{project_id}/monetization")
async def get_monetization_settings(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get monetization settings for a project."""
    from ...infrastructure.repositories.models import (
        ProjectMonetizationDB,
        VideoProjectDB,
    )

    project = session.get(VideoProjectDB, project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    monetization = session.exec(
        select(ProjectMonetizationDB).where(
            ProjectMonetizationDB.project_id == project_id
        )
    ).first()

    if not monetization:
        return {
            "tips_enabled": True,
            "subscriptions_enabled": False,
            "suggested_tip_amounts": [1, 5, 10, 20],
            "subscription_price": 9.99,
            "subscription_tier_name": "Premium",
        }

    import json

    return {
        "tips_enabled": monetization.tips_enabled,
        "subscriptions_enabled": monetization.subscriptions_enabled,
        "suggested_tip_amounts": json.loads(monetization.suggested_tip_amounts),
        "subscription_price": monetization.subscription_price,
        "subscription_tier_name": monetization.subscription_tier_name,
    }


@router.put("/projects/{project_id}/monetization")
async def update_monetization_settings(
    project_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Update monetization settings for a project."""
    from ...infrastructure.repositories.models import (
        ProjectMonetizationDB,
        VideoProjectDB,
    )

    project = session.get(VideoProjectDB, project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    body = await request.json()

    monetization = session.exec(
        select(ProjectMonetizationDB).where(
            ProjectMonetizationDB.project_id == project_id
        )
    ).first()

    if not monetization:
        monetization = ProjectMonetizationDB(
            project_id=project_id,
            tips_enabled=body.get("tips_enabled", True),
            subscriptions_enabled=body.get("subscriptions_enabled", False),
            suggested_tip_amounts=str(
                body.get("suggested_tip_amounts", [1, 5, 10, 20])
            ),
            subscription_price=body.get("subscription_price", 9.99),
            subscription_tier_name=body.get("subscription_tier_name", "Premium"),
        )
        session.add(monetization)
    else:
        if "tips_enabled" in body:
            monetization.tips_enabled = body["tips_enabled"]
        if "subscriptions_enabled" in body:
            monetization.subscriptions_enabled = body["subscriptions_enabled"]
        if "suggested_tip_amounts" in body:
            monetization.suggested_tip_amounts = str(body["suggested_tip_amounts"])
        if "subscription_price" in body:
            monetization.subscription_price = body["subscription_price"]
        if "subscription_tier_name" in body:
            monetization.subscription_tier_name = body["subscription_tier_name"]
        session.add(monetization)

    session.commit()

    import json

    return {
        "success": True,
        "tips_enabled": monetization.tips_enabled,
        "subscriptions_enabled": monetization.subscriptions_enabled,
        "suggested_tip_amounts": json.loads(monetization.suggested_tip_amounts),
        "subscription_price": monetization.subscription_price,
        "subscription_tier_name": monetization.subscription_tier_name,
    }


@router.post("/projects/{project_id}/publish")
async def publish_project(
    project_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
    session: Session = Depends(get_session),
):
    """Publish a project as a video."""
    from ...infrastructure.repositories.models import VideoProjectDB

    project = session.get(VideoProjectDB, project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    if project.status == "published":
        raise HTTPException(status_code=400, detail="Project already published")

    body = await request.json()
    visibility = body.get("visibility", "public")

    project.status = "published"
    project.published_at = datetime.utcnow()
    project.permission = visibility
    session.add(project)
    session.commit()

    return {
        "success": True,
        "message": "Project published successfully",
        "project_id": project_id,
        "published_at": project.published_at.isoformat(),
    }


@router.post("/projects/{project_id}/export")
async def export_project(
    project_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
    session: Session = Depends(get_session),
):
    """Export a project (placeholder - actual rendering would be async)."""
    from ...infrastructure.repositories.models import VideoProjectDB

    project = session.get(VideoProjectDB, project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    body = await request.json()
    format = body.get("format", "mp4")
    quality = body.get("quality", "1080p")

    return {
        "success": True,
        "message": "Export started",
        "project_id": project_id,
        "export_settings": {
            "format": format,
            "quality": quality,
            "status": "processing",
        },
    }


@router.get("/projects/{project_id}/export-status")
async def get_export_status(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get export status for a project."""
    from ...infrastructure.repositories.models import VideoProjectDB

    project = session.get(VideoProjectDB, project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "project_id": project_id,
        "export_status": "completed"
        if project.status == "published"
        else "not_started",
        "video_url": project.thumbnail_url,
    }


@router.post("/projects/{project_id}/duplicate")
async def duplicate_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
    session: Session = Depends(get_session),
):
    """Duplicate a project."""
    from ...infrastructure.repositories.models import VideoProjectDB
    import uuid

    original = session.get(VideoProjectDB, project_id)
    if not original or original.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    duplicate = VideoProjectDB(
        id=str(uuid.uuid4()),
        user_id=current_user["id"],
        title=f"{original.title} (Copy)",
        description=original.description,
        status="draft",
        duration=original.duration,
    )
    session.add(duplicate)
    session.commit()

    return {
        "success": True,
        "project_id": duplicate.id,
        "message": "Project duplicated successfully",
    }


# ==================== Advanced Video Editing Endpoints ====================


@router.post("/projects/{project_id}/tracks/{track_id}/keyframes")
async def add_keyframe(
    project_id: str,
    track_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Add a keyframe to a track."""
    from ...infrastructure.repositories.models import VideoEditorKeyframeDB

    project = session.get(VideoProjectDB, project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    body = await request.json()
    keyframe = VideoEditorKeyframeDB(
        project_id=project_id,
        track_id=track_id,
        property_name=body.get("property_name"),
        time=body.get("time", 0.0),
        value=json.dumps(body.get("value")),
        easing=body.get("easing", "linear"),
    )
    session.add(keyframe)
    session.commit()

    return {"success": True, "keyframe_id": keyframe.id}


@router.get("/projects/{project_id}/tracks/{track_id}/keyframes")
async def get_keyframes(
    project_id: str,
    track_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get all keyframes for a track."""
    project = session.get(VideoProjectDB, project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    keyframes = session.exec(
        select(VideoEditorKeyframeDB).where(VideoEditorKeyframeDB.track_id == track_id)
    ).all()

    return {
        "keyframes": [
            {
                "id": kf.id,
                "property_name": kf.property_name,
                "time": kf.time,
                "value": json.loads(kf.value),
                "easing": kf.easing,
            }
            for kf in keyframes
        ]
    }


@router.delete("/keyframes/{keyframe_id}")
async def delete_keyframe(
    keyframe_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Delete a keyframe."""
    keyframe = session.get(VideoEditorKeyframeDB, keyframe_id)
    if not keyframe:
        raise HTTPException(status_code=404, detail="Keyframe not found")

    project = session.get(VideoProjectDB, keyframe.project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    session.delete(keyframe)
    session.commit()

    return {"success": True}


@router.post("/projects/{project_id}/tracks/{track_id}/color-grade")
async def set_color_grade(
    project_id: str,
    track_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Set color grading for a track."""
    from ...infrastructure.repositories.models import VideoEditorColorGradeDB

    project = session.get(VideoProjectDB, project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    body = await request.json()

    existing = session.exec(
        select(VideoEditorColorGradeDB).where(
            VideoEditorColorGradeDB.track_id == track_id
        )
    ).first()

    if existing:
        for key in [
            "brightness",
            "contrast",
            "saturation",
            "temperature",
            "tint",
            "highlights",
            "shadows",
            "vibrance",
            "filters",
        ]:
            if key in body:
                setattr(
                    existing,
                    key,
                    json.dumps(body[key]) if key == "filters" else body[key],
                )
        existing.updated_at = datetime.utcnow()
        session.add(existing)
        session.commit()
        return {"success": True, "color_grade_id": existing.id}

    color_grade = VideoEditorColorGradeDB(
        project_id=project_id,
        track_id=track_id,
        brightness=body.get("brightness", 0.0),
        contrast=body.get("contrast", 0.0),
        saturation=body.get("saturation", 0.0),
        temperature=body.get("temperature", 0.0),
        tint=body.get("tint", 0.0),
        highlights=body.get("highlights", 0.0),
        shadows=body.get("shadows", 0.0),
        vibrance=body.get("vibrance", 0.0),
        filters=json.dumps(body.get("filters", [])),
    )
    session.add(color_grade)
    session.commit()

    return {"success": True, "color_grade_id": color_grade.id}


@router.get("/projects/{project_id}/tracks/{track_id}/color-grade")
async def get_color_grade(
    project_id: str,
    track_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get color grading for a track."""
    project = session.get(VideoProjectDB, project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    color_grade = session.exec(
        select(VideoEditorColorGradeDB).where(
            VideoEditorColorGradeDB.track_id == track_id
        )
    ).first()

    if not color_grade:
        return {"brightness": 0.0, "contrast": 0.0, "saturation": 0.0}

    return {
        "brightness": color_grade.brightness,
        "contrast": color_grade.contrast,
        "saturation": color_grade.saturation,
        "temperature": color_grade.temperature,
        "tint": color_grade.tint,
        "highlights": color_grade.highlights,
        "shadows": color_grade.shadows,
        "vibrance": color_grade.vibrance,
        "filters": json.loads(color_grade.filters) if color_grade.filters else [],
    }


@router.post("/projects/{project_id}/tracks/{track_id}/audio-mix")
async def set_audio_mix(
    project_id: str,
    track_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Set audio mixing for a track."""
    from ...infrastructure.repositories.models import VideoEditorAudioMixDB

    project = session.get(VideoProjectDB, project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    body = await request.json()

    existing = session.exec(
        select(VideoEditorAudioMixDB).where(VideoEditorAudioMixDB.track_id == track_id)
    ).first()

    if existing:
        for key in [
            "volume",
            "pan",
            "mute",
            "solo",
            "fade_in",
            "fade_out",
            "equalizer",
            "audio_effects",
            "duck_others",
        ]:
            if key in body:
                setattr(
                    existing,
                    key,
                    json.dumps(body[key])
                    if key in ["equalizer", "audio_effects"]
                    else body[key],
                )
        existing.updated_at = datetime.utcnow()
        session.add(existing)
        session.commit()
        return {"success": True, "audio_mix_id": existing.id}

    audio_mix = VideoEditorAudioMixDB(
        project_id=project_id,
        track_id=track_id,
        volume=body.get("volume", 1.0),
        pan=body.get("pan", 0.0),
        mute=body.get("mute", False),
        solo=body.get("solo", False),
        fade_in=body.get("fade_in", 0.0),
        fade_out=body.get("fade_out", 0.0),
        equalizer=json.dumps(body.get("equalizer", {"low": 0, "mid": 0, "high": 0})),
        audio_effects=json.dumps(body.get("audio_effects", [])),
        duck_others=body.get("duck_others", False),
    )
    session.add(audio_mix)
    session.commit()

    return {"success": True, "audio_mix_id": audio_mix.id}


@router.get("/projects/{project_id}/tracks/{track_id}/audio-mix")
async def get_audio_mix(
    project_id: str,
    track_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get audio mixing for a track."""
    project = session.get(VideoProjectDB, project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    audio_mix = session.exec(
        select(VideoEditorAudioMixDB).where(VideoEditorAudioMixDB.track_id == track_id)
    ).first()

    if not audio_mix:
        return {"volume": 1.0, "pan": 0.0, "mute": False, "solo": False}

    return {
        "volume": audio_mix.volume,
        "pan": audio_mix.pan,
        "mute": audio_mix.mute,
        "solo": audio_mix.solo,
        "fade_in": audio_mix.fade_in,
        "fade_out": audio_mix.fade_out,
        "equalizer": json.loads(audio_mix.equalizer)
        if audio_mix.equalizer
        else {"low": 0, "mid": 0, "high": 0},
        "audio_effects": json.loads(audio_mix.audio_effects)
        if audio_mix.audio_effects
        else [],
        "duck_others": audio_mix.duck_others,
    }


@router.post("/projects/{project_id}/tracks/{track_id}/chroma-key")
async def set_chroma_key(
    project_id: str,
    track_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Set chroma key (green screen) settings for a track."""
    from ...infrastructure.repositories.models import VideoEditorChromaKeyDB

    project = session.get(VideoProjectDB, project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    body = await request.json()

    existing = session.exec(
        select(VideoEditorChromaKeyDB).where(
            VideoEditorChromaKeyDB.track_id == track_id
        )
    ).first()

    if existing:
        for key in [
            "enabled",
            "key_color",
            "similarity",
            "smoothness",
            "spill_suppression",
            "background_type",
            "background_value",
        ]:
            if key in body:
                setattr(existing, key, body[key])
        existing.updated_at = datetime.utcnow()
        session.add(existing)
        session.commit()
        return {"success": True, "chroma_key_id": existing.id}

    chroma_key = VideoEditorChromaKeyDB(
        project_id=project_id,
        track_id=track_id,
        enabled=body.get("enabled", False),
        key_color=body.get("key_color", "#00FF00"),
        similarity=body.get("similarity", 0.4),
        smoothness=body.get("smoothness", 0.1),
        spill_suppression=body.get("spill_suppression", 0.1),
        background_type=body.get("background_type", "none"),
        background_value=body.get("background_value"),
    )
    session.add(chroma_key)
    session.commit()

    return {"success": True, "chroma_key_id": chroma_key.id}


@router.get("/projects/{project_id}/tracks/{track_id}/chroma-key")
async def get_chroma_key(
    project_id: str,
    track_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get chroma key settings for a track."""
    project = session.get(VideoProjectDB, project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    chroma_key = session.exec(
        select(VideoEditorChromaKeyDB).where(
            VideoEditorChromaKeyDB.track_id == track_id
        )
    ).first()

    if not chroma_key:
        return {"enabled": False, "key_color": "#00FF00", "similarity": 0.4}

    return {
        "enabled": chroma_key.enabled,
        "key_color": chroma_key.key_color,
        "similarity": chroma_key.similarity,
        "smoothness": chroma_key.smoothness,
        "spill_suppression": chroma_key.spill_suppression,
        "background_type": chroma_key.background_type,
        "background_value": chroma_key.background_value,
    }


@router.post("/projects/{project_id}/tracks/{track_id}/effects")
async def add_effect(
    project_id: str,
    track_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Add an effect to a track."""
    from ...infrastructure.repositories.models import VideoEditorEffectDB

    project = session.get(VideoProjectDB, project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    body = await request.json()
    effect = VideoEditorEffectDB(
        project_id=project_id,
        track_id=track_id,
        effect_type=body.get("effect_type"),
        parameters=json.dumps(body.get("parameters", {})),
        start_time=body.get("start_time", 0.0),
        end_time=body.get("end_time", 0.0),
        enabled=body.get("enabled", True),
    )
    session.add(effect)
    session.commit()

    return {"success": True, "effect_id": effect.id}


@router.get("/projects/{project_id}/tracks/{track_id}/effects")
async def get_effects(
    project_id: str,
    track_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get all effects for a track."""
    project = session.get(VideoProjectDB, project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    effects = session.exec(
        select(VideoEditorEffectDB).where(VideoEditorEffectDB.track_id == track_id)
    ).all()

    return {
        "effects": [
            {
                "id": eff.id,
                "effect_type": eff.effect_type,
                "parameters": json.loads(eff.parameters),
                "start_time": eff.start_time,
                "end_time": eff.end_time,
                "enabled": eff.enabled,
            }
            for eff in effects
        ]
    }


@router.delete("/effects/{effect_id}")
async def delete_effect(
    effect_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Delete an effect."""
    effect = session.get(VideoEditorEffectDB, effect_id)
    if not effect:
        raise HTTPException(status_code=404, detail="Effect not found")

    project = session.get(VideoProjectDB, effect.project_id)
    if not project or project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    session.delete(effect)
    session.commit()

    return {"success": True}
