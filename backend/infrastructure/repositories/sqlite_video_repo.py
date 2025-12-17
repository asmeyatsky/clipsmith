from typing import List, Optional
from sqlmodel import Session, select
from ...domain.entities.video import Video
from ...domain.ports.repository_ports import VideoRepositoryPort
from .database import engine
from .models import VideoDB

class SQLiteVideoRepository(VideoRepositoryPort):
    async def save(self, video: Video) -> Video:
        with Session(engine) as session:
            # Check if exists to update, or create new
            # For simplicity in this phase, we assume create if not exists or overwrite
            # Since our entities are immutable-ish data classes in domain, mapping is direct
            
            video_db = VideoDB.model_validate(video)
            video_db = session.merge(video_db)
            session.commit()
            session.refresh(video_db)
            return Video(**video_db.model_dump())

    async def get_by_id(self, video_id: str) -> Optional[Video]:
        with Session(engine) as session:
            video_db = session.get(VideoDB, video_id)
            if video_db:
                return Video(**video_db.model_dump())
            return None

    async def find_all(self) -> List[Video]:
        with Session(engine) as session:
            statement = select(VideoDB)
            results = session.exec(statement).all()
            return [Video(**v.model_dump()) for v in results]

    async def list_by_creator(self, creator_id: str) -> List[Video]:
        with Session(engine) as session:
            statement = select(VideoDB).where(VideoDB.creator_id == creator_id)
            results = session.exec(statement).all()
            return [Video(**v.model_dump()) for v in results]
