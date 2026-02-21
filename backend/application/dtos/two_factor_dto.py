from pydantic import BaseModel, field_validator
from typing import Optional
from enum import Enum


class TwoFactorMethod(str, Enum):
    TOTP = "totp"
    EMAIL = "email"


class TwoFactorSetupRequestDTO(BaseModel):
    method: TwoFactorMethod


class TwoFactorSetupResponseDTO(BaseModel):
    secret: str
    qr_code: str
    backup_codes: list[str]


class TwoFactorVerifyRequestDTO(BaseModel):
    code: str
    method: TwoFactorMethod


class TwoFactorDisableRequestDTO(BaseModel):
    password: str


class TwoFactorStatusResponseDTO(BaseModel):
    enabled: bool
    method: Optional[TwoFactorMethod] = None
