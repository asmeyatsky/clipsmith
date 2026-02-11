import json
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated, List, Optional
from ...application.services.video_editor_service import VideoEditorService
from ...infrastructure.repositories.sqlite_video_editor_repo import (
    SQLiteVideoEditorRepository,
)
from ...infrastructure.repositories.database import get_session
from ...infrastructure.security.jwt_adapter import JWTAdapter
from sqlmodel import Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
):
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
