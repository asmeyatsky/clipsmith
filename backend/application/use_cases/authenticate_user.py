from typing import Optional
from ...domain.ports.repository_ports import UserRepositoryPort
from ...infrastructure.security.security_adapter import PasswordHelper
from ...infrastructure.security.jwt_adapter import JWTAdapter
from ..dtos.auth_dto import LoginRequestDTO, LoginResponseDTO, UserResponseDTO
from datetime import timedelta

class AuthenticateUserUseCase:
    def __init__(self, user_repo: UserRepositoryPort):
        self._user_repo = user_repo

    def execute(self, dto: LoginRequestDTO) -> Optional[LoginResponseDTO]:
        # Get user
        user = self._user_repo.get_by_email(dto.email)
        if not user:
            return None

        # Verify password
        if not PasswordHelper.verify_password(dto.password, user.hashed_password):
            return None

        # Create Token
        access_token = JWTAdapter.create_access_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=timedelta(minutes=60)
        )

        return LoginResponseDTO(
            access_token=access_token,
            user=UserResponseDTO(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active
            )
        )
