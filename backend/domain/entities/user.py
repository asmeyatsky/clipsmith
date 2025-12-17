from dataclasses import dataclass
from ..base import Entity

@dataclass(frozen=True, kw_only=True)
class User(Entity):
    username: str
    email: str
    hashed_password: str = "" # Default empty for now, or make optional
    is_active: bool = True
