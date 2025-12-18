from pydantic import BaseModel, EmailStr

class RegisterRequestDTO(BaseModel):
    username: str
    email: EmailStr
    password: str

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
