from fastapi import APIRouter, Depends, HTTPException, status
from ...domain.ports.repository_ports import UserRepositoryPort, VideoRepositoryPort
from ...infrastructure.repositories.sqlite_user_repo import SQLiteUserRepository
from ...infrastructure.repositories.sqlite_video_repo import SQLiteVideoRepository
from ...application.use_cases.get_user_profile import GetUserProfileUseCase
from ...application.dtos.profile_dto import ProfileResponseDTO

router = APIRouter(prefix="/users", tags=["users"])

# Dependency Injection Helpers
from ...infrastructure.repositories.database import get_session
from sqlmodel import Session

def get_user_repo(session: Session = Depends(get_session)) -> UserRepositoryPort:
    return SQLiteUserRepository(session)

def get_video_repo(session: Session = Depends(get_session)) -> VideoRepositoryPort:
    return SQLiteVideoRepository(session)

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
