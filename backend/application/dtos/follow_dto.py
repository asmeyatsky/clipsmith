from pydantic import BaseModel
from datetime import datetime

class FollowResponseDTO(BaseModel):
    follower_id: str
    followed_id: str
    created_at: datetime

class FollowStatusDTO(BaseModel):
    is_following: bool
