from dataclasses import dataclass
from datetime import datetime
from ..base import Entity

@dataclass(frozen=True, kw_only=True)
class Tip(Entity):
    sender_id: str
    receiver_id: str
    video_id: str | None = None
    amount: float
    currency: str = "USD"
    created_at: datetime = datetime.now()
