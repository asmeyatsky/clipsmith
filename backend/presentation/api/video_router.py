import math
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import Annotated, List
from fastapi.security import OAuth2PasswordBearer

from ...infrastructure.queue import get_video_queue
from ...application.tasks import generate_captions_task

from ...domain.ports.repository_ports import (
    VideoRepositoryPort,
    UserRepositoryPort,
    TipRepositoryPort,
    CaptionRepositoryPort,
)
from ...domain.ports.storage_port import StoragePort
from ...infrastructure.repositories.sqlite_video_repo import SQLiteVideoRepository
from ...infrastructure.repositories.sqlite_user_repo import SQLiteUserRepository
from ...infrastructure.repositories.sqlite_tip_repo import SQLiteTipRepository
from ...infrastructure.repositories.sqlite_caption_repo import SQLiteCaptionRepository
from ...infrastructure.adapters.storage_factory import get_storage_adapter
from ...application.use_cases.upload_video import UploadVideoUseCase
from ...application.use_cases.list_videos import ListVideosUseCase
from ...application.use_cases.get_video_by_id import GetVideoByIdUseCase
from ...application.use_cases.send_tip import SendTipUseCase
from ...application.dtos.video_dto import (
    VideoCreateDTO,
    VideoResponseDTO,
    PaginatedVideoResponseDTO,
)
from ...application.dtos.tip_dto import TipCreateDTO, TipResponseDTO
from ...application.dtos.caption_dto import CaptionResponseDTO
from ...infrastructure.security.jwt_adapter import JWTAdapter

router = APIRouter(prefix="/videos", tags=["videos"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Dependency Injection Helpers
from ...infrastructure.repositories.database import get_session
from sqlmodel import Session
from ...infrastructure.repositories.sqlite_interaction_repo import (
    SQLiteInteractionRepository,
)
from ...application.dtos.interaction_dto import CommentRequestDTO, CommentResponseDTO


def get_video_repo(session: Session = Depends(get_session)) -> VideoRepositoryPort:
    return SQLiteVideoRepository(session)


def get_user_repo(session: Session = Depends(get_session)) -> UserRepositoryPort:
    return SQLiteUserRepository(session)


def get_interaction_repo(
    session: Session = Depends(get_session),
) -> SQLiteInteractionRepository:
    return SQLiteInteractionRepository(session)


def get_tip_repo(session: Session = Depends(get_session)) -> TipRepositoryPort:
    return SQLiteTipRepository(session)


def get_caption_repo(session: Session = Depends(get_session)) -> CaptionRepositoryPort:
    return SQLiteCaptionRepository(session)


def get_storage_adapter_dep() -> StoragePort:
    return get_storage_adapter()


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repo: UserRepositoryPort = Depends(get_user_repo),
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )

    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return {"user_id": user.id, "username": user.username}


@router.get("/", response_model=PaginatedVideoResponseDTO)
def list_videos(
    page: int = 1,
    page_size: int = 20,
    repo: VideoRepositoryPort = Depends(get_video_repo),
):
    use_case = ListVideosUseCase(repo)
    return use_case.execute(page=page, page_size=page_size)


@router.get("/search", response_model=PaginatedVideoResponseDTO)
def search_videos(
    q: str,
    page: int = 1,
    page_size: int = 20,
    repo: VideoRepositoryPort = Depends(get_video_repo),
):
    offset = (page - 1) * page_size
    videos = repo.search(q, offset=offset, limit=page_size)
    total = repo.count_search(q)

    video_responses = [
        VideoResponseDTO(
            id=v.id,
            title=v.title,
            description=v.description,
            creator_id=v.creator_id,
            url=v.url,
            thumbnail_url=v.thumbnail_url,
            status=v.status,
            views=v.views,
            likes=v.likes,
            duration=v.duration,
            created_at=v.created_at,
        )
        for v in videos
    ]

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedVideoResponseDTO(
        items=video_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# File validation constants
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
ALLOWED_CONTENT_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
    "video/webm",
    "video/x-m4v",
}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB


def validate_video_file(file: UploadFile) -> None:
    """Validate uploaded video file for size and format."""
    # Check content type
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    # Check file extension
    if file.filename:
        import os as os_path

        _, ext = os_path.splitext(file.filename.lower())
        if ext not in ALLOWED_VIDEO_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension. Allowed extensions: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}",
            )

    # Check file size by reading content length or seeking to end
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)} MB",
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file uploaded"
        )


@router.post("/", response_model=VideoResponseDTO)
def upload_video(
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    current_user: Annotated[dict, Depends(get_current_user)],
    repo: VideoRepositoryPort = Depends(get_video_repo),
    storage: StoragePort = Depends(get_storage_adapter_dep),
):
    # Validate the uploaded file
    validate_video_file(file)

    # DTO creation from form data
    dto = VideoCreateDTO(
        title=title, description=description, creator_id=current_user["user_id"]
    )

    use_case = UploadVideoUseCase(repo, storage)
    return use_case.execute(dto, file.file, file.filename)


@router.get("/{video_id}", response_model=VideoResponseDTO)
def get_video_by_id(video_id: str, repo: VideoRepositoryPort = Depends(get_video_repo)):
    use_case = GetVideoByIdUseCase(repo)
    video = use_case.execute(video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )
    return video


@router.post("/{video_id}/view")
def increment_video_views(
    video_id: str, repo: VideoRepositoryPort = Depends(get_video_repo)
):
    video = repo.increment_views(video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )
    return {"views": video.views}


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(
    video_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    repo: VideoRepositoryPort = Depends(get_video_repo),
    storage: StoragePort = Depends(get_storage_adapter),
):
    # Get video first to check ownership
    video = repo.get_by_id(video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    # Check if current user is the creator
    if video.creator_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this video",
        )

    # Delete video files from storage
    if video.url:
        storage.delete(video.url)
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
    repo: SQLiteInteractionRepository = Depends(get_interaction_repo),
    video_repo: VideoRepositoryPort = Depends(get_video_repo),
):
    user_id = current_user["user_id"]

    # Check if already liked to determine if this is a new like or unlike
    existing_like = repo.get_like(user_id, video_id)
    is_liked = repo.toggle_like(user_id, video_id)

    # Send notification for new likes only
    if is_liked and not existing_like:
        try:
            from ...application.services.notification_service import NotificationService
            from ...domain.entities.notification import NotificationType

            video = video_repo.get_by_id(video_id)
            if (
                video and video.creator_id != user_id
            ):  # Don't notify if liking own video
                notification_service = NotificationService(
                    notification_repo=repo,  # type: ignore - using interaction repo for simplicity
                    user_repo=None,  # type: ignore
                    video_repo=video_repo,
                )

                notification = notification_service.create_like_notification(
                    video_id, user_id, video.creator_id
                )
                notification_service.send_notification(notification)
        except Exception as e:
            # Log error but don't fail the request
            import logging
            logging.getLogger(__name__).warning("Failed to send like notification: %s", e)

    return {"message": "Success", "is_liked": is_liked}


@router.get("/{video_id}/like-status")
def get_like_status(
    video_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    repo: SQLiteInteractionRepository = Depends(get_interaction_repo),
):
    user_id = current_user["user_id"]
    has_liked = repo.has_user_liked(user_id, video_id)
    return {"has_liked": has_liked}


@router.post("/{video_id}/comments", response_model=CommentResponseDTO)
def add_comment(
    video_id: str,
    comment_data: CommentRequestDTO,
    current_user: Annotated[dict, Depends(get_current_user)],
    repo: SQLiteInteractionRepository = Depends(get_interaction_repo),
    video_repo: VideoRepositoryPort = Depends(get_video_repo),
):
    user_id = current_user["user_id"]
    username = current_user["username"]

    comment = repo.add_comment(user_id, username, video_id, comment_data.content)

    # Send notification for new comment
    try:
        from ...application.services.notification_service import NotificationService
        from ...domain.entities.notification import NotificationType

        video = video_repo.get_by_id(video_id)
        if (
            video and video.creator_id != user_id
        ):  # Don't notify if commenting on own video
            notification_service = NotificationService(
                notification_repo=repo,  # type: ignore - using interaction repo for simplicity
                user_repo=None,  # type: ignore
                video_repo=video_repo,
            )

            notification = notification_service.create_comment_notification(
                video_id, user_id, video.creator_id, comment_data.content
            )
            notification_service.send_notification(notification)
    except Exception as e:
        logging.getLogger(__name__).warning("Failed to send comment notification: %s", e)

    return CommentResponseDTO(
        id=comment.id,
        video_id=comment.video_id,
        username=comment.username,
        content=comment.content,
        created_at=comment.created_at,
    )


@router.get("/{video_id}/comments", response_model=List[CommentResponseDTO])
def list_comments(
    video_id: str, repo: SQLiteInteractionRepository = Depends(get_interaction_repo)
):
    comments = repo.list_comments(video_id)
    return [
        CommentResponseDTO(
            id=c.id,
            video_id=c.video_id,
            username=c.username,
            content=c.content,
            created_at=c.created_at,
        )
        for c in comments
    ]


@router.post("/{video_id}/captions/generate", status_code=status.HTTP_202_ACCEPTED)
def trigger_caption_generation(
    video_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    video_repo: VideoRepositoryPort = Depends(get_video_repo),
):
    video = video_repo.get_by_id(video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    if video.creator_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate captions for this video",
        )

    if video.status != "READY" or not video.url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video is not ready for caption generation",
        )

    video_queue = get_video_queue()
    video_queue.enqueue(
        generate_captions_task,
        video_id,
        job_timeout=3600,  # 1 hour timeout
    )

    return {"message": "Caption generation started", "video_id": video_id}


@router.get("/{video_id}/captions", response_model=List[CaptionResponseDTO])
def get_video_captions(
    video_id: str,
    video_repo: VideoRepositoryPort = Depends(get_video_repo),
    caption_repo: CaptionRepositoryPort = Depends(get_caption_repo),
):
    video = video_repo.get_by_id(video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    captions = caption_repo.get_by_video_id(video_id)
    return [
        CaptionResponseDTO(
            id=c.id,
            video_id=c.video_id,
            text=c.text,
            start_time=c.start_time,
            end_time=c.end_time,
            language=c.language,
        )
        for c in captions
    ]


@router.post(
    "/{video_id}/tip",
    response_model=TipResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
def send_tip_to_video_creator(
    video_id: str,
    tip_data: TipCreateDTO,
    current_user: Annotated[dict, Depends(get_current_user)],
    user_repo: UserRepositoryPort = Depends(get_user_repo),
    video_repo: VideoRepositoryPort = Depends(get_video_repo),
    tip_repo: TipRepositoryPort = Depends(get_tip_repo),
):
    # Ensure the tip is for the video's creator
    video = video_repo.get_by_id(video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    if video.creator_id != tip_data.receiver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receiver ID must be the video creator's ID",
        )

    if current_user["user_id"] == tip_data.receiver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot tip yourself"
        )

    use_case = SendTipUseCase(user_repo, tip_repo, video_repo)
    try:
        tip_data.video_id = video_id  # Ensure video_id is set in DTO
        return use_case.execute(tip_data, current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
