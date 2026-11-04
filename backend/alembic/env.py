"""Entorno de Alembic: le dice cómo conectarse a la base y cuáles son los modelos.

Alembic ejecuta este archivo cada vez que se corre `alembic upgrade` o `downgrade`.
"""

from logging.config import fileConfig

from sqlalchemy import create_engine, pool

# Importar los modelos registra todas las tablas en Base.metadata (lo usa `autogenerate`).
import app.modelos  # noqa: F401
from alembic import context
from app.db import Base
from app.modelos.utilidades import obtener_url_base_datos

# Objeto de configuración de Alembic (lee alembic.ini).
config = context.config

# Configura el registro de mensajes. disable_existing_loggers=False evita silenciar
# los mensajes de pytest cuando las pruebas ejecutan Alembic desde Python.
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# Metadatos de los modelos: Alembic los compara con la base real.
target_metadata = Base.metadata


def _obtener_url():
    """Devuelve la URL de la base: la que pasen las pruebas o DATABASE_URL.

    Las pruebas la entregan en config.attributes["url"] (así no hay que escribir la
    contraseña en texto). Desde la terminal se lee de DATABASE_URL o de backend/.env.
    """
    url = config.attributes.get("url") or obtener_url_base_datos()
    if not url:
        raise RuntimeError(
            "Falta DATABASE_URL. Defínela en el entorno o en backend/.env "
            "(ejemplo: postgresql+psycopg://postgres:CONTRASENA@localhost:5432/postgres)."
        )
    return url


def run_migrations_offline() -> None:
    """Modo "sin conexión": en vez de ejecutar, imprime el SQL (alembic upgrade head --sql)."""
    context.configure(
        url=_obtener_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Modo normal: se conecta a la base y ejecuta las migraciones."""
    # NullPool: no deja conexiones abiertas al terminar (importante para borrar bases de prueba).
    motor = create_engine(_obtener_url(), poolclass=pool.NullPool)
    with motor.connect() as conexion:
        context.configure(
            connection=conexion,
            target_metadata=target_metadata,
            compare_type=True,  # también detecta cambios de tipo de columna
        )
        # En PostgreSQL todo el cambio de esquema va en una sola transacción:
        # o se aplica completo o no se aplica nada.
        with context.begin_transaction():
            context.run_migrations()
    motor.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
