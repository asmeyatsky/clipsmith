from typing import Optional
from sqlmodel import Session, select
from ...domain.entities.user import User
from ...domain.ports.repository_ports import UserRepositoryPort
from .models import UserDB
from .database import engine

class SQLiteUserRepository(UserRepositoryPort):
    def __init__(self):
        # In a real app we'd inject the session
        pass

    async def save(self, user: User) -> User:
        with Session(engine) as session:
            db_user = UserDB(
                id=user.id,
                username=user.username,
                email=user.email,
                hashed_password=user.hashed_password,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            db_user = session.merge(db_user)
            session.commit()
            session.refresh(db_user)
            return user

    async def get_by_email(self, email: str) -> Optional[User]:
        with Session(engine) as session:
            statement = select(UserDB).where(UserDB.email == email)
            result = session.exec(statement).first()
            if result:
                return User(
                    id=result.id,
                    username=result.username,
                    email=result.email,
                    hashed_password=result.hashed_password,
                    is_active=result.is_active,
                    created_at=result.created_at,
                    updated_at=result.updated_at
                )
            return None

    async def get_by_id(self, user_id: str) -> Optional[User]:
        with Session(engine) as session:
            result = session.get(UserDB, user_id)
            if result:
                return User(
                    id=result.id,
                    username=result.username,
                    email=result.email,
                    hashed_password=result.hashed_password,
                    is_active=result.is_active,
                    created_at=result.created_at,
                    updated_at=result.updated_at
                )
            return None

    async def get_by_username(self, username: str) -> Optional[User]:
        with Session(engine) as session:
            statement = select(UserDB).where(UserDB.username == username)
            result = session.exec(statement).first()
            if result:
                return User(
                    id=result.id,
                    username=result.username,
                    email=result.email,
                    hashed_password=result.hashed_password,
                    is_active=result.is_active,
                    created_at=result.created_at,
                    updated_at=result.updated_at
                )
            return None
