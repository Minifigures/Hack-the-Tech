from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from .config import settings

# `check_same_thread` is a SQLite-only knob. Setting it on Postgres throws.
_is_sqlite = settings.EVALFORGE_DB_URL.startswith("sqlite")
connect_args: dict = {"check_same_thread": False} if _is_sqlite else {}

# Serverless functions can't keep persistent pools. Use pre-ping + recycle
# to survive Supabase's idle connection eviction, and a tiny pool because
# each invocation is single-threaded.
if _is_sqlite:
    engine = create_engine(settings.EVALFORGE_DB_URL, connect_args=connect_args)
else:
    engine = create_engine(
        settings.EVALFORGE_DB_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=2,
        max_overflow=3,
    )


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
