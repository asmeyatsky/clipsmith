import os
from typing import Generator
from contextlib import contextmanager
from sqlmodel import create_engine, SQLModel, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")

# SQLite needs check_same_thread=False; PostgreSQL does not
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

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
