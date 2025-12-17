from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import Annotated, List
from fastapi.security import OAuth2PasswordBearer

from ...domain.ports.repository_ports import VideoRepositoryPort
from ...domain.ports.storage_port import StoragePort
from ...infrastructure.repositories.sqlite_video_repo import SQLiteVideoRepository
from ...infrastructure.adapters.file_storage_adapter import FileSystemStorageAdapter
from ...application.use_cases.upload_video import UploadVideoUseCase
from ...application.use_cases.list_videos import ListVideosUseCase
from ...application.dtos.video_dto import VideoCreateDTO, VideoResponseDTO
from ...infrastructure.security.jwt_adapter import JWTAdapter

router = APIRouter(prefix="/videos", tags=["videos"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Dependency Injection Helpers
def get_video_repo() -> VideoRepositoryPort:
    return SQLiteVideoRepository()

def get_storage_adapter() -> StoragePort:
    return FileSystemStorageAdapter()

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    payload = JWTAdapter.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

@router.get("/", response_model=List[VideoResponseDTO])
async def list_videos(repo: VideoRepositoryPort = Depends(get_video_repo)):
    use_case = ListVideosUseCase(repo)
    return await use_case.execute()

@router.post("/", response_model=VideoResponseDTO)
async def upload_video(
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
    return await use_case.execute(dto, file.file, file.filename)

# --- Interactions ---
from ...infrastructure.repositories.sqlite_interaction_repo import SQLiteInteractionRepository
from ...application.dtos.interaction_dto import CommentRequestDTO, CommentResponseDTO

def get_interaction_repo() -> SQLiteInteractionRepository:
    return SQLiteInteractionRepository()

@router.post("/{video_id}/like")
async def toggle_like(
    video_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    repo: SQLiteInteractionRepository = Depends(get_interaction_repo)
):
    user_id = current_user["user_id"]
    is_liked = await repo.toggle_like(user_id, video_id)
    return {"message": "Success", "is_liked": is_liked}

@router.get("/{video_id}/like-status")
async def get_like_status(
    video_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    repo: SQLiteInteractionRepository = Depends(get_interaction_repo)
):
    user_id = current_user["user_id"]
    has_liked = await repo.has_user_liked(user_id, video_id)
    return {"has_liked": has_liked}

@router.post("/{video_id}/comments", response_model=CommentResponseDTO)
async def add_comment(
    video_id: str,
    comment_data: CommentRequestDTO,
    current_user: Annotated[dict, Depends(get_current_user)],
    repo: SQLiteInteractionRepository = Depends(get_interaction_repo)
):
    user_id = current_user["user_id"]
    # We need username, let's grab it from somewhere. 
    # The JWT payload might have it? Let's check auth_router.
    # JWT payload currently has: sub (email?), user_id.
    # We might need to fetch user, or just store user_id and fetch username lazily.
    # For now, let's just use email from 'sub' or query the user.
    # Re-using user_id is safer.
    # Actually, let's just make the user repo a dependency here too if we really want username.
    # Short cut: pass "Anonymous" or fetch user. 
    # Let's inspect JWT payload construction in auth_router/authenticate_user.
    
    # Assuming we update JWT to include username or we fetch it.
    # Let's just fetch the user for now to get the username correctly.
    # Imports inside function to avoid circular, or just import UserRepo.
    from ...infrastructure.repositories.sqlite_user_repo import SQLiteUserRepository
    user_repo = SQLiteUserRepository()
    user = await user_repo.get_by_id(user_id)
    username = user.username if user else "Unknown"

    comment = await repo.add_comment(user_id, username, video_id, comment_data.content)
    return CommentResponseDTO(
        id=comment.id,
        video_id=comment.video_id,
        username=comment.username,
        content=comment.content,
        created_at=comment.created_at
    )

@router.get("/{video_id}/comments", response_model=List[CommentResponseDTO])
async def list_comments(
    video_id: str,
    repo: SQLiteInteractionRepository = Depends(get_interaction_repo)
):
    comments = await repo.list_comments(video_id)
    return [
        CommentResponseDTO(
            id=c.id,
            video_id=c.video_id,
            username=c.username,
            content=c.content,
            created_at=c.created_at
        ) for c in comments
    ]
