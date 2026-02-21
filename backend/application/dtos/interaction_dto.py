from pydantic import BaseModel, field_validator
from datetime import datetime
from ..utils.sanitization import sanitize_input, MAX_COMMENT_LENGTH


class CommentRequestDTO(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Comment cannot be empty")
        if len(v) > MAX_COMMENT_LENGTH:
            raise ValueError(f"Comment cannot exceed {MAX_COMMENT_LENGTH} characters")
        return sanitize_input(v.strip())


class CommentResponseDTO(BaseModel):
    id: str
    video_id: str
    username: str
    content: str
    created_at: datetime
