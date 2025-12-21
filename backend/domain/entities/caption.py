from dataclasses import dataclass
from ..base import Entity

@dataclass(frozen=True, kw_only=True)
class Caption(Entity):
    video_id: str
    text: str
    start_time: float # In seconds
    end_time: float   # In seconds
    language: str = "en"
