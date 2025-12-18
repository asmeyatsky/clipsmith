from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import Annotated, List
from fastapi.security import OAuth2PasswordBearer

from ...domain.ports.repository_ports import VideoRepositoryPort, UserRepositoryPort
from ...domain.ports.storage_port import StoragePort
from ...infrastructure.repositories.sqlite_video_repo import SQLiteVideoRepository
from ...infrastructure.repositories.sqlite_user_repo import SQLiteUserRepository
from ...infrastructure.adapters.file_storage_adapter import FileSystemStorageAdapter
from ...application.use_cases.upload_video import UploadVideoUseCase
from ...application.use_cases.list_videos import ListVideosUseCase
from ...application.use_cases.get_video_by_id import GetVideoByIdUseCase
from ...application.dtos.video_dto import VideoCreateDTO, VideoResponseDTO, PaginatedVideoResponseDTO
from ...infrastructure.security.jwt_adapter import JWTAdapter

router = APIRouter(prefix="/videos", tags=["videos"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Dependency Injection Helpers
from ...infrastructure.repositories.database import get_session
from sqlmodel import Session
from ...infrastructure.repositories.sqlite_interaction_repo import SQLiteInteractionRepository
from ...application.dtos.interaction_dto import CommentRequestDTO, CommentResponseDTO

def get_video_repo(session: Session = Depends(get_session)) -> VideoRepositoryPort:
    return SQLiteVideoRepository(session)

def get_user_repo(session: Session = Depends(get_session)) -> UserRepositoryPort:
    return SQLiteUserRepository(session)

def get_interaction_repo(session: Session = Depends(get_session)) -> SQLiteInteractionRepository:
    return SQLiteInteractionRepository(session)

def get_storage_adapter() -> StoragePort:
    return FileSystemStorageAdapter()

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repo: UserRepositoryPort = Depends(get_user_repo)
):
    payload = JWTAdapter.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID not found in token")

    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
    return {"user_id": user.id, "username": user.username}

@router.get("/", response_model=PaginatedVideoResponseDTO)
def list_videos(
    page: int = 1,
    page_size: int = 20,
    repo: VideoRepositoryPort = Depends(get_video_repo)
):
    use_case = ListVideosUseCase(repo)
    return use_case.execute(page=page, page_size=page_size)

@router.post("/", response_model=VideoResponseDTO)
def upload_video(
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    current_user: Annotated[dict, Depends(get_current_user)],
    repo: VideoRepositoryPort = Depends(get_video_repo),
    storage: StoragePort = Depends(get_storage_adapter)
):
    # DTO creation from form data
    dto = VideoCreateDTO(
        title=title,
        description=description,
        creator_id=current_user["user_id"]
    )
    
    use_case = UploadVideoUseCase(repo, storage)
    return use_case.execute(dto, file.file, file.filename)

@router.get("/{video_id}", response_model=VideoResponseDTO)
def get_video_by_id(
    video_id: str,
    repo: VideoRepositoryPort = Depends(get_video_repo)
):
    use_case = GetVideoByIdUseCase(repo)
    video = use_case.execute(video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return video

@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(
    video_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    repo: VideoRepositoryPort = Depends(get_video_repo),
    storage: StoragePort = Depends(get_storage_adapter)
):
    # Get video first to check ownership
    video = repo.get_by_id(video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    # Check if current user is the creator
    if video.creator_id != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this video")

    # Delete video files from storage
    if video.video_url:
        storage.delete(video.video_url)
    if video.thumbnail_url:
        storage.delete(video.thumbnail_url)

    # Delete video record from database
    repo.delete(video_id)
    return None

# --- Interactions ---

@router.post("/{video_id}/like")
def toggle_like(
    video_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    repo: SQLiteInteractionRepository = Depends(get_interaction_repo)
):
    user_id = current_user["user_id"]
    is_liked = repo.toggle_like(user_id, video_id)
    return {"message": "Success", "is_liked": is_liked}

@router.get("/{video_id}/like-status")
def get_like_status(
    video_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    repo: SQLiteInteractionRepository = Depends(get_interaction_repo)
):
    user_id = current_user["user_id"]
    has_liked = repo.has_user_liked(user_id, video_id)
    return {"has_liked": has_liked}

@router.post("/{video_id}/comments", response_model=CommentResponseDTO)
def add_comment(
    video_id: str,
    comment_data: CommentRequestDTO,
    current_user: Annotated[dict, Depends(get_current_user)],
    repo: SQLiteInteractionRepository = Depends(get_interaction_repo)
):
    user_id = current_user["user_id"]
    username = current_user["username"]

    comment = repo.add_comment(user_id, username, video_id, comment_data.content)
    return CommentResponseDTO(
        id=comment.id,
        video_id=comment.video_id,
        username=comment.username,
        content=comment.content,
        created_at=comment.created_at
    )

@router.get("/{video_id}/comments", response_model=List[CommentResponseDTO])
def list_comments(
    video_id: str,
    repo: SQLiteInteractionRepository = Depends(get_interaction_repo)
):
    comments = repo.list_comments(video_id)
    return [
        CommentResponseDTO(
            id=c.id,
            video_id=c.video_id,
            username=c.username,
            content=c.content,
            created_at=c.created_at
        ) for c in comments
    ]