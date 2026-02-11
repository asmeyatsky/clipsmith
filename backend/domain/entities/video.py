from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, TypeVar
from uuid import UUID
from ..base import Entity


class VideoStatus(str, Enum):
    UPLOADING = "UPLOADING"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


@dataclass(frozen=True, kw_only=True)
class Video(Entity):
    title: str = ""
    description: str = ""
    creator_id: str = ""
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    status: str = "PENDING"
    views: int = 0
    likes: int = 0
    duration: float = 0.0


@dataclass(frozen=True, kw_only=True)
class VideoMetadata:
    """Enhanced metadata container for video processing and AI analysis."""
    
    processing_confidence: float = field(default=0.0)
    hashtags: List[str] = field(default_factory=list)
    content_flags: List[str] = field(default_factory=list)
    ai_analysis: Dict[str, Any] = field(default_factory=dict)
    moderation_status: Optional[str] = field(default=None)
    processing_duration: float = field(default=0.0)
    file_size: int = field(default=0)
    resolution_info: Dict[str, Any] = field(default_factory=dict)
    ai_confidence_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "auto_approve_threshold": 0.9,
        "auto_reject_threshold": 0.7,
        "flag_for_review": 0.6,
    })
    
    def __init__(
        self,
        processing_confidence=0.0,
        hashtags=[],
        content_flags=[],
        ai_analysis={},
        moderation_status=None,
        processing_duration=0.0,
        file_size=0,
        resolution_info={}
    ):
        pass
    
    def add_hashtag(self, hashtag: str) -> None:
        """Add a hashtag to video metadata."""
        if not self.hashtags:
            self.hashtags = []
        self.hashtags.append(hashtag)
    
    def add_content_flag(self, flag_type: str) -> None:
        """Add a content violation flag."""
        if not self.content_flags:
            self.content_flags.append(flag_type)
    
    def set_moderation_status(self, status: Optional[str]) -> None:
        """Set moderation status."""
        self.moderation_status = status
    
    def update_processing_info(self, duration: float) -> None:
        """Update video processing information."""
        self.processing_duration = duration
        self.processing_confidence = confidence
    
    def update_ai_analysis(self, confidence: float, labels: Dict[str, Any]) -> None:
        """Update AI analysis results."""
        self.processing_confidence = confidence
        self.ai_labels.update(labels)
    
    def get_hashtags(self) -> List[str]:
        """Get hashtags from metadata."""
        return self.hashtags.copy()
    
    def get_content_flags(self) -> List[str]:
        """Get content flags from metadata."""
        return self.content_flags.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "processing_confidence": self.processing_confidence,
            "hashtags": self.hashtags,
            "content_flags": self.content_flags,
            "ai_analysis": self.ai_analysis,
            "moderation_status": self.moderation_status,
            "processing_duration": self.processing_duration,
            "file_size": self.file_size,
            "resolution_info": self.resolution_info
        }