from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ...infrastructure.repositories.sqlite_user_repo import SQLiteUserRepository
from ...application.use_cases.register_user import RegisterUserUseCase
from ...application.use_cases.authenticate_user import AuthenticateUserUseCase
from ...application.dtos.auth_dto import RegisterRequestDTO, LoginRequestDTO, TokenResponseDTO, UserResponseDTO

router = APIRouter(prefix="/auth", tags=["auth"])

# Dependency Injection Helper
def get_user_repo():
    return SQLiteUserRepository()

@router.post("/register", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
async def register(
    dto: RegisterRequestDTO,
    repo: SQLiteUserRepository = Depends(get_user_repo)
):
    try:
        use_case = RegisterUserUseCase(repo)
        return await use_case.execute(dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=TokenResponseDTO)
async def login(
    dto: LoginRequestDTO,
    repo: SQLiteUserRepository = Depends(get_user_repo)
):
    use_case = AuthenticateUserUseCase(repo)
    token = await use_case.execute(dto)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token
