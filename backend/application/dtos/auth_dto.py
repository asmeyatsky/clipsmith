from pydantic import BaseModel, EmailStr, field_validator
from ..utils.sanitization import sanitize_input, MAX_USERNAME_LENGTH


class RegisterRequestDTO(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Username cannot be empty")
        if len(v) > MAX_USERNAME_LENGTH:
            raise ValueError(f"Username cannot exceed {MAX_USERNAME_LENGTH} characters")
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return sanitize_input(v.strip())


class LoginRequestDTO(BaseModel):
    email: EmailStr
    password: str


class TokenResponseDTO(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponseDTO(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool


class LoginResponseDTO(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponseDTO


class PasswordResetRequestDTO(BaseModel):
    email: EmailStr


class PasswordResetConfirmDTO(BaseModel):
    token: str
    new_password: str
