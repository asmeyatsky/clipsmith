from ...domain.entities.user import User
from ...domain.ports.repository_ports import UserRepositoryPort
from ...infrastructure.security.security_adapter import PasswordHelper
from ..dtos.auth_dto import RegisterRequestDTO, UserResponseDTO
import uuid

class RegisterUserUseCase:
    def __init__(self, user_repo: UserRepositoryPort):
        self._user_repo = user_repo

    def execute(self, dto: RegisterRequestDTO) -> UserResponseDTO:
        # Check if user exists
        existing_user = self._user_repo.get_by_email(dto.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Hash password
        hashed_pw = PasswordHelper.get_password_hash(dto.password)

        # Create Domain Entity
        new_user = User(
            id=str(uuid.uuid4()),
            username=dto.username,
            email=dto.email,
            hashed_password=hashed_pw
        )

        # Save to Repo
        saved_user = self._user_repo.save(new_user)

        return UserResponseDTO(
            id=saved_user.id,
            username=saved_user.username,
            email=saved_user.email,
            is_active=saved_user.is_active
        )
