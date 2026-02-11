from typing import Annotated, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ...domain.ports.repository_ports import (
    VideoRepositoryPort,
    InteractionRepositoryPort,
    UserRepositoryPort,
)
from ...infrastructure.repositories.sqlite_video_repo import SQLiteVideoRepository
from ...infrastructure.repositories.sqlite_interaction_repo import (
    SQLiteInteractionRepository,
)
from ...infrastructure.repositories.sqlite_user_repo import SQLiteUserRepository
from ...application.use_cases.get_personalized_feed import GetPersonalizedFeedUseCase
from ...application.dtos.video_dto import VideoResponseDTO, PaginatedVideoResponseDTO
from ...infrastructure.security.jwt_adapter import JWTAdapter

router = APIRouter(prefix="/feed", tags=["feed"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Dependency Injection Helpers
from ...infrastructure.repositories.database import get_session
from sqlmodel import Session


def get_video_repo(session: Session = Depends(get_session)) -> VideoRepositoryPort:
    return SQLiteVideoRepository(session)


def get_interaction_repo(
    session: Session = Depends(get_session),
) -> InteractionRepositoryPort:
    return SQLiteInteractionRepository(session)


def get_user_repo(session: Session = Depends(get_session)) -> UserRepositoryPort:
    return SQLiteUserRepository(session)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repo: UserRepositoryPort = Depends(get_user_repo),
):
    payload = JWTAdapter.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user = user_repo.get_by_id(payload.get("sub"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


@router.get("/", response_model=PaginatedVideoResponseDTO)
def get_feed(
    feed_type: Annotated[
        str, Query(description="Feed type: foryou, following, trending")
    ] = "foryou",
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Videos per page")] = 20,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    video_repo: VideoRepositoryPort = Depends(get_video_repo),
    interaction_repo: InteractionRepositoryPort = Depends(get_interaction_repo),
    user_repo: UserRepositoryPort = Depends(get_user_repo),
):
    """
    Get personalized video feed.

    - **foryou**: Personalized recommendations based on viewing history and preferences
    - **following**: Videos from creators you follow
    - **trending**: Popular videos in the last 24 hours
    """

    # Validate feed type
    valid_feed_types = ["foryou", "following", "trending"]
    if feed_type not in valid_feed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid feed type. Must be one of: {', '.join(valid_feed_types)}",
        )

    # For anonymous users, only show trending
    if not current_user and feed_type != "trending":
        feed_type = "trending"

    # Get personalized feed
    feed_use_case = GetPersonalizedFeedUseCase(video_repo, interaction_repo, user_repo)

    if current_user:
        user_id = current_user.id
        videos = feed_use_case.execute(user_id, feed_type, page, page_size)
        total_count = feed_use_case.get_feed_count(user_id, feed_type)
    else:
        # For anonymous users, just return recent videos
        videos = video_repo.find_all(offset=(page - 1) * page_size, limit=page_size)
        total_count = video_repo.count_all()

    # Convert to response DTOs
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

    # Calculate pagination
    total_pages = (total_count + page_size - 1) // page_size

    return PaginatedVideoResponseDTO(
        items=video_responses,
        total=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/trending", response_model=PaginatedVideoResponseDTO)
def get_trending_feed(
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Videos per page")] = 20,
    video_repo: VideoRepositoryPort = Depends(get_video_repo),
):
    """
    Get trending videos from the last 24 hours.
    This endpoint doesn't require authentication.
    """
    # Fetch only the page we need, sorted by engagement at the DB level
    offset = (page - 1) * page_size
    all_videos = video_repo.find_all(offset=0, limit=200)

    # Sort by engagement score (views + likes * 5)
    trending_videos = sorted(
        all_videos, key=lambda v: (v.views + v.likes * 5), reverse=True
    )

    # Apply pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_videos = trending_videos[start_idx:end_idx]

    # Convert to response DTOs
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
        for v in paginated_videos
    ]

    total_count = len(trending_videos)
    total_pages = (total_count + page_size - 1) // page_size

    return PaginatedVideoResponseDTO(
        items=video_responses,
        total=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
