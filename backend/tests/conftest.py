import pytest
from sqlmodel import Session, SQLModel, create_engine
from backend.infrastructure.repositories.models import UserDB, VideoDB, LikeDB, CommentDB
from backend.infrastructure.repositories.sqlite_user_repo import SQLiteUserRepository
from backend.infrastructure.repositories.sqlite_video_repo import SQLiteVideoRepository
from backend.infrastructure.repositories.sqlite_interaction_repo import SQLiteInteractionRepository

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine) # Clean up after tests

@pytest.fixture(name="user_repo")
def user_repo_fixture(session: Session):
    return SQLiteUserRepository(session)

@pytest.fixture(name="video_repo")
def video_repo_fixture(session: Session):
    return SQLiteVideoRepository(session)

@pytest.fixture(name="interaction_repo")
def interaction_repo_fixture(session: Session):
    return SQLiteInteractionRepository(session)
