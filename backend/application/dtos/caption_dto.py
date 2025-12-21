from pydantic import BaseModel
from typing import List

class CaptionResponseDTO(BaseModel):
    id: str
    video_id: str
    text: str
    start_time: float
    end_time: float
    language: str
