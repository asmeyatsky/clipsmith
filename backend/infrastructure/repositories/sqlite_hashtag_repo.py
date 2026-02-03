from typing import List, Optional
from sqlmodel import Session, select, func, and_, desc
from ...domain.entities.hashtag import Hashtag
from ...domain.ports.repository_ports import HashtagRepositoryPort
from .database import engine
from .models import HashtagDB


class SQLiteHashtagRepository(HashtagRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def save(self, hashtag: Hashtag) -> Hashtag:
        hashtag_db = HashtagDB.model_validate(hashtag)
        hashtag_db = self.session.merge(hashtag_db)
        self.session.commit()
        self.session.refresh(hashtag_db)
        return Hashtag(**hashtag_db.model_dump())

    def get_by_name(self, name: str) -> Optional[Hashtag]:
        hashtag_db = self.session.get(HashtagDB, name)
        if hashtag_db:
            return Hashtag(**hashtag_db.model_dump())
        return None

    def get_trending_hashtags(self, limit: int = 50) -> List[Hashtag]:
        """Get hashtags sorted by trending score."""
        statement = (
            select(HashtagDB).order_by(desc(HashtagDB.trending_score)).limit(limit)
        )
        results = self.session.exec(statement).all()
        return [Hashtag(**h.model_dump()) for h in results]

    def get_popular_hashtags(self, limit: int = 50) -> List[Hashtag]:
        """Get hashtags sorted by usage count."""
        statement = select(HashtagDB).order_by(desc(HashtagDB.count)).limit(limit)
        results = self.session.exec(statement).all()
        return [Hashtag(**h.model_dump()) for h in results]

    def search_hashtags(self, query: str, limit: int = 20) -> List[Hashtag]:
        """Search hashtags by name."""
        search_pattern = f"%{query}%"
        statement = (
            select(HashtagDB)
            .where(HashtagDB.name.ilike(search_pattern))
            .order_by(desc(HashtagDB.trending_score))
            .limit(limit)
        )
        results = self.session.exec(statement).all()
        return [Hashtag(**h.model_dump()) for h in results]

    def update_hashtag_usage(self, hashtag_name: str) -> Optional[Hashtag]:
        """Increment usage count and last used timestamp."""
        from datetime import datetime

        hashtag_db = self.session.get(HashtagDB, hashtag_name)
        if not hashtag_db:
            # Create new hashtag
            new_hashtag = Hashtag(
                name=hashtag_name, count=1, last_used_at=datetime.utcnow()
            )
            hashtag_db = HashtagDB.model_validate(new_hashtag)
            hashtag_db = self.session.merge(hashtag_db)
        else:
            # Update existing hashtag
            hashtag_db.count += 1
            hashtag_db.last_used_at = datetime.utcnow()
            self.session.add(hashtag_db)

        self.session.commit()
        self.session.refresh(hashtag_db)
        return Hashtag(**hashtag_db.model_dump())

    def update_trending_scores(self, hashtag_scores: dict[str, float]) -> int:
        """Update trending scores for multiple hashtags."""
        updated_count = 0

        for hashtag_name, score in hashtag_scores.items():
            hashtag_db = self.session.get(HashtagDB, hashtag_name)
            if hashtag_db:
                hashtag_db.trending_score = score
                self.session.add(hashtag_db)
                updated_count += 1

        if updated_count > 0:
            self.session.commit()

        return updated_count

    def get_recent_hashtags(self, hours: int = 24, limit: int = 20) -> List[Hashtag]:
        """Get recently used hashtags."""
        from datetime import datetime, timedelta

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        statement = (
            select(HashtagDB)
            .where(HashtagDB.last_used_at >= cutoff_time)
            .order_by(desc(HashtagDB.last_used_at))
            .limit(limit)
        )
        results = self.session.exec(statement).all()
        return [Hashtag(**h.model_dump()) for h in results]
