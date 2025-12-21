from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated # Ensure Annotated is imported

from ...domain.ports.repository_ports import UserRepositoryPort, VideoRepositoryPort, FollowRepositoryPort
from ...infrastructure.repositories.sqlite_user_repo import SQLiteUserRepository
from ...infrastructure.repositories.sqlite_video_repo import SQLiteVideoRepository
from ...infrastructure.repositories.sqlite_follow_repo import SQLiteFollowRepository
from ...application.use_cases.get_user_profile import GetUserProfileUseCase
from ...application.use_cases.manage_follows import ManageFollowsUseCase
from ...application.dtos.profile_dto import ProfileResponseDTO
from ...application.dtos.follow_dto import FollowResponseDTO, FollowStatusDTO
from ...infrastructure.security.jwt_adapter import JWTAdapter # For get_current_user

router = APIRouter(prefix="/users", tags=["users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Dependency Injection Helpers
from ...infrastructure.repositories.database import get_session
from sqlmodel import Session

def get_user_repo(session: Session = Depends(get_session)) -> UserRepositoryPort:
    return SQLiteUserRepository(session)

def get_video_repo(session: Session = Depends(get_session)) -> VideoRepositoryPort:
    return SQLiteVideoRepository(session)

def get_follow_repo(session: Session = Depends(get_session)) -> FollowRepositoryPort:
    return SQLiteFollowRepository(session)

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

    return {"user_id": user.id, "username": user.username} # Return dict for consistency with video_router

@router.get("/{username}", response_model=ProfileResponseDTO)
def get_user_profile(
    username: str,
    user_repo: UserRepositoryPort = Depends(get_user_repo),
    video_repo: VideoRepositoryPort = Depends(get_video_repo)
):
    try:
        use_case = GetUserProfileUseCase(user_repo, video_repo)
        return use_case.execute(username)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{user_id}/follow", response_model=FollowResponseDTO, status_code=status.HTTP_201_CREATED)
def follow_user(
    user_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    user_repo: UserRepositoryPort = Depends(get_user_repo),
    follow_repo: FollowRepositoryPort = Depends(get_follow_repo)
):
    use_case = ManageFollowsUseCase(user_repo, follow_repo)
    try:
        return use_case.follow(current_user["user_id"], user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(
    user_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    user_repo: UserRepositoryPort = Depends(get_user_repo),
    follow_repo: FollowRepositoryPort = Depends(get_follow_repo)
):
    use_case = ManageFollowsUseCase(user_repo, follow_repo)
    try:
        if not use_case.unfollow(current_user["user_id"], user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow relationship not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{user_id}/follow_status", response_model=FollowStatusDTO)
def get_user_follow_status(
    user_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    user_repo: UserRepositoryPort = Depends(get_user_repo),
    follow_repo: FollowRepositoryPort = Depends(get_follow_repo)
):
    use_case = ManageFollowsUseCase(user_repo, follow_repo)
    return use_case.get_follow_status(current_user["user_id"], user_id)
