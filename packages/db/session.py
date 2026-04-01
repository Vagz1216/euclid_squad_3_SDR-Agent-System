"""Engine and session factory."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from packages.db.bootstrap import bootstrap_sqlite_file
from packages.db.models import Base
from packages.shared.settings import ensure_data_dir, get_settings

_engine = None
_SessionLocal = None


def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        url = settings.database_url
        if url.startswith("sqlite"):
            bootstrap_sqlite_file(url)
        else:
            ensure_data_dir(url)
        _engine = create_engine(url, echo=False, future=True)
        if not url.startswith("sqlite"):
            Base.metadata.create_all(_engine)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def get_session_factory():
    get_engine()
    return _SessionLocal


def session_scope() -> Generator[Session, None, None]:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
