from pydantic import BaseModel
from datetime import datetime

class CommentRequestDTO(BaseModel):
    content: str

class CommentResponseDTO(BaseModel):
    id: str
    video_id: str
    username: str
    content: str
    created_at: datetime
