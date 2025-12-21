from typing import List, Optional
from sqlmodel import Session, select
from ...domain.entities.tip import Tip
from ...domain.ports.repository_ports import TipRepositoryPort
from .models import TipDB

class SQLiteTipRepository(TipRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def save(self, tip: Tip) -> Tip:
        tip_db = TipDB.model_validate(tip)
        self.session.add(tip_db)
        self.session.commit()
        self.session.refresh(tip_db)
        return Tip(**tip_db.model_dump())

    def get_tips_by_receiver_id(self, receiver_id: str) -> List[Tip]:
        statement = select(TipDB).where(TipDB.receiver_id == receiver_id).order_by(TipDB.created_at.desc())
        results = self.session.exec(statement).all()
        return [Tip(**t.model_dump()) for t in results]

    def get_tips_by_sender_id(self, sender_id: str) -> List[Tip]:
        statement = select(TipDB).where(TipDB.sender_id == sender_id).order_by(TipDB.created_at.desc())
        results = self.session.exec(statement).all()
        return [Tip(**t.model_dump()) for t in results]

    def get_tips_by_video_id(self, video_id: str) -> List[Tip]:
        statement = select(TipDB).where(TipDB.video_id == video_id).order_by(TipDB.created_at.desc())
        results = self.session.exec(statement).all()
        return [Tip(**t.model_dump()) for t in results]
