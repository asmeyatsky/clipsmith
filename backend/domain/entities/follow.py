from dataclasses import dataclass
from datetime import datetime
from ..base import Entity

@dataclass(frozen=True, kw_only=True)
class Follow(Entity):
    follower_id: str
    followed_id: str
    created_at: datetime = datetime.now()
