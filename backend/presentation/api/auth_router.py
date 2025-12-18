from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from ...infrastructure.repositories.sqlite_user_repo import SQLiteUserRepository
from ...application.use_cases.register_user import RegisterUserUseCase
from ...application.use_cases.authenticate_user import AuthenticateUserUseCase
from ...application.dtos.auth_dto import RegisterRequestDTO, LoginRequestDTO, LoginResponseDTO, UserResponseDTO
from ...infrastructure.repositories.database import get_session
from ...infrastructure.security.jwt_adapter import JWTAdapter
from sqlmodel import Session
from ...domain.ports.repository_ports import UserRepositoryPort


router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Dependency Injection Helper
def get_user_repo(session: Session = Depends(get_session)) -> UserRepositoryPort:
    return SQLiteUserRepository(session)

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

    return user

@router.post("/register", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
def register(
    dto: RegisterRequestDTO,
    repo: UserRepositoryPort = Depends(get_user_repo)
):
    try:
        use_case = RegisterUserUseCase(repo)
        return use_case.execute(dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=LoginResponseDTO)
def login(
    dto: LoginRequestDTO,
    repo: UserRepositoryPort = Depends(get_user_repo)
):
    use_case = AuthenticateUserUseCase(repo)
    result = use_case.execute(dto)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result

@router.get("/me", response_model=UserResponseDTO)
def get_me(
    current_user = Depends(get_current_user)
):
    return UserResponseDTO(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active
    )
