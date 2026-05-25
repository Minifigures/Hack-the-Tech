from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from .config import settings

connect_args = {"check_same_thread": False} if settings.EVALFORGE_DB_URL.startswith("sqlite") else {}
engine = create_engine(settings.EVALFORGE_DB_URL, connect_args=connect_args)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
