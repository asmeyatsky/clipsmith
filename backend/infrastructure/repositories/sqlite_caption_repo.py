from typing import List, Optional
from sqlmodel import Session, select
from ...domain.entities.caption import Caption
from ...domain.ports.repository_ports import CaptionRepositoryPort
from .models import CaptionDB

class SQLiteCaptionRepository(CaptionRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def save(self, caption: Caption) -> Caption:
        caption_db = CaptionDB.model_validate(caption)
        self.session.add(caption_db)
        self.session.commit()
        self.session.refresh(caption_db)
        return Caption(**caption_db.model_dump())

    def get_by_video_id(self, video_id: str) -> List[Caption]:
        statement = select(CaptionDB).where(CaptionDB.video_id == video_id).order_by(CaptionDB.start_time)
        results = self.session.exec(statement).all()
        return [Caption(**c.model_dump()) for c in results]

    def delete_by_video_id(self, video_id: str) -> bool:
        statement = select(CaptionDB).where(CaptionDB.video_id == video_id)
        results = self.session.exec(statement).all()
        if results:
            for caption_db in results:
                self.session.delete(caption_db)
            self.session.commit()
            return True
        return False
