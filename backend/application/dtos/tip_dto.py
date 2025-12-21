from pydantic import BaseModel
from datetime import datetime

class TipCreateDTO(BaseModel):
    receiver_id: str
    video_id: str | None = None
    amount: float
    currency: str = "USD"

class TipResponseDTO(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    video_id: str | None
    amount: float
    currency: str
    created_at: datetime
