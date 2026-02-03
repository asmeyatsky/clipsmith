from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import List, Optional
import uuid


@dataclass(frozen=True, kw_only=True)
class Hashtag:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    count: int = 0  # Number of times this hashtag has been used
    trending_score: float = 0.0  # Calculated trending score
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None

    def increment_usage(self) -> "Hashtag":
        """Increment usage count and update last used timestamp."""
        return replace(self, count=self.count + 1, last_used_at=datetime.utcnow())

    def update_trending_score(self, score: float) -> "Hashtag":
        """Update trending score based on recent activity."""
        return replace(self, trending_score=score)
