from typing import Generator
from contextlib import contextmanager
from sqlmodel import create_engine, SQLModel, Session

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency injection compatible session generator."""
    with Session(engine) as session:
        yield session

@contextmanager
def get_task_session():
    """Context manager for getting a session in background tasks."""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
