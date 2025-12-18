from typing import List, Optional
from sqlmodel import Session, select, func
from ...domain.entities.video import Video
from ...domain.ports.repository_ports import VideoRepositoryPort
from .database import engine
from .models import VideoDB

class SQLiteVideoRepository(VideoRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def save(self, video: Video) -> Video:
        video_db = VideoDB.model_validate(video)
        video_db = self.session.merge(video_db)
        self.session.commit()
        self.session.refresh(video_db)
        return Video(**video_db.model_dump())

    def get_by_id(self, video_id: str) -> Optional[Video]:
        video_db = self.session.get(VideoDB, video_id)
        if video_db:
            return Video(**video_db.model_dump())
        return None

    def find_all(self, offset: int = 0, limit: int = 20) -> List[Video]:
        statement = select(VideoDB).order_by(VideoDB.created_at.desc()).offset(offset).limit(limit)
        results = self.session.exec(statement).all()
        return [Video(**v.model_dump()) for v in results]

    def count_all(self) -> int:
        statement = select(func.count()).select_from(VideoDB)
        return self.session.exec(statement).one()

    def list_by_creator(self, creator_id: str) -> List[Video]:
        statement = select(VideoDB).where(VideoDB.creator_id == creator_id).order_by(VideoDB.created_at.desc())
        results = self.session.exec(statement).all()
        return [Video(**v.model_dump()) for v in results]

    def delete(self, video_id: str) -> bool:
        video_db = self.session.get(VideoDB, video_id)
        if video_db:
            self.session.delete(video_db)
            self.session.commit()
            return True
        return False
