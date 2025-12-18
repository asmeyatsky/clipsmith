from typing import Optional
from sqlmodel import Session, select
from ...domain.entities.user import User
from ...domain.ports.repository_ports import UserRepositoryPort
from .models import UserDB
from .database import engine # Keep for now

class SQLiteUserRepository(UserRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def save(self, user: User) -> User:
        db_user = UserDB.model_validate(user) # Use model_validate for cleaner mapping
        db_user = self.session.merge(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return User(**db_user.model_dump())

    def get_by_email(self, email: str) -> Optional[User]:
        statement = select(UserDB).where(UserDB.email == email)
        result = self.session.exec(statement).first()
        if result:
            return User(**result.model_dump())
        return None

    def get_by_id(self, user_id: str) -> Optional[User]:
        result = self.session.get(UserDB, user_id)
        if result:
            return User(**result.model_dump())
        return None

    def get_by_username(self, username: str) -> Optional[User]:
        statement = select(UserDB).where(UserDB.username == username)
        result = self.session.exec(statement).first()
        if result:
            return User(**result.model_dump())
        return None
