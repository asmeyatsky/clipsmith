import pytest
from sqlmodel import Session, SQLModel, create_engine
from fastapi.testclient import TestClient
from backend.infrastructure.repositories.models import UserDB, VideoDB, LikeDB, CommentDB, CaptionDB, PasswordResetDB
from backend.infrastructure.repositories.sqlite_user_repo import SQLiteUserRepository
from backend.infrastructure.repositories.sqlite_video_repo import SQLiteVideoRepository
from backend.infrastructure.repositories.sqlite_interaction_repo import SQLiteInteractionRepository
from backend.infrastructure.repositories.sqlite_caption_repo import SQLiteCaptionRepository
from backend.infrastructure.repositories.sqlite_follow_repo import SQLiteFollowRepository
from backend.main import app
from backend.infrastructure.repositories.database import get_session

@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session

@pytest.fixture(name="user_repo")
def user_repo_fixture(session: Session):
    return SQLiteUserRepository(session)

@pytest.fixture(name="video_repo")
def video_repo_fixture(session: Session):
    return SQLiteVideoRepository(session)

@pytest.fixture(name="interaction_repo")
def interaction_repo_fixture(session: Session):
    return SQLiteInteractionRepository(session)

@pytest.fixture(name="caption_repo")
def caption_repo_fixture(session: Session):
    return SQLiteCaptionRepository(session)

@pytest.fixture(name="client")
def client_fixture(engine):
    def get_test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
