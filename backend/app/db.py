"""Base declarativa, motor y sesión compartidos por los módulos."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import configuracion


class Base(DeclarativeBase):
    pass


engine = create_engine(configuracion.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Cierra la sesión al terminar la petición; cada servicio decide cuándo confirmar."""
    with SessionLocal() as session:
        yield session
