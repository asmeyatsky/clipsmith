from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional
from ...application.services.video_editor_service import VideoEditorService
from ...infrastructure.repositories.sqlite_video_editor_repo import (
    SQLiteVideoEditorRepository,
)
from ...infrastructure.repositories.database import get_session
from ...presentation.middleware.security import get_current_user
from sqlmodel import Session

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
    project = await service.create_project(
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
    projects = await service.get_user_projects(
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
    project = await service.get_project(project_id)
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
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    updated_project = await service.update_project_title(project_id, title)
    return {"success": True, "project": updated_project}


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Delete a project."""
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    success = await service.delete_project(project_id)
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
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Here you would typically upload the file to cloud storage
    # For now, we'll simulate with a URL
    import os
    import uuid

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

    asset = await service.upload_asset(
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
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    assets = await service.get_project_assets(project_id, asset_type)
    return {"success": True, "assets": assets}


@router.delete("/assets/{asset_id}")
async def delete_asset(
    asset_id: str,
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Delete an asset."""
    # TODO: Check if asset belongs to user
    success = await service.delete_asset(asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")

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
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    import json

    transition_params = json.loads(parameters) if parameters else None

    transition = await service.add_transition(
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
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    transitions = await service.get_project_transitions(project_id)
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
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    track = await service.add_track(
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
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    tracks = await service.get_project_tracks(project_id)
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
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    caption = await service.add_caption(
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
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    captions = await service.get_project_captions(project_id, video_asset_id)
    return {"success": True, "captions": captions}


@router.delete("/captions/{caption_id}")
async def delete_caption(
    caption_id: str,
    current_user: dict = Depends(get_current_user),
    service: VideoEditorService = Depends(get_video_editor_service),
):
    """Delete a caption."""
    # TODO: Check if caption belongs to user
    success = await service.delete_caption(caption_id)
    if not success:
        raise HTTPException(status_code=404, detail="Caption not found")

    return {"success": success}
