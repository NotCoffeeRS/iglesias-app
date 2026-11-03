"""Pruebas de los modelos `iglesias` y `usuarios` y de su migración (Issue #4, primer PR).

Estas pruebas necesitan PostgreSQL de verdad (no SQLite): los CHECK, el índice sobre
lower(nombre_usuario) y las llaves foráneas se comportan distinto. Si no hay una
DATABASE_URL de PostgreSQL, las pruebas FALLAN con un mensaje claro (no se saltan).

Cada prueba trabaja en una base temporal que se crea y se borra sola, así que no toca
tus datos.
"""

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, delete, inspect, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.db import Base
from app.modelos import CARGOS, Iglesia, Usuario
from app.modelos.utilidades import obtener_url_base_datos

# Ruta de backend/alembic.ini (este archivo está en backend/tests/).
RUTA_ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"

MENSAJE_SIN_POSTGRES = (
    "No hay una base PostgreSQL configurada para las pruebas. Define DATABASE_URL en el "
    "entorno o en backend/.env, por ejemplo: "
    "postgresql+psycopg://postgres:TU_CONTRASENA@localhost:5432/postgres . "
    "Estas pruebas no se saltan ni se ejecutan con SQLite a propósito: la versión de "
    "PostgreSQL de desarrollo debe ser la misma que la de Neon."
)

MENSAJE_SIN_CONEXION = (
    "No se pudo crear la base temporal de pruebas en PostgreSQL. Revisa que el servicio "
    "esté corriendo, que la contraseña de DATABASE_URL sea la correcta y que ese usuario "
    "pueda crear bases de datos (CREATEDB)."
)


@pytest.fixture(scope="module")
def url_servidor() -> URL:
    """URL del servidor PostgreSQL; si no hay una, la prueba falla con un mensaje claro."""
    texto = obtener_url_base_datos()
    if not texto or not texto.startswith("postgresql"):
        pytest.fail(MENSAJE_SIN_POSTGRES, pytrace=False)
    return make_url(texto)


@contextmanager
def _base_temporal(url_servidor: URL) -> Iterator[URL]:
    """Crea una base vacía con nombre único, la entrega y al final la borra."""
    # Nombre aleatorio y seguro (solo letras, números y guion bajo) para no chocar con nada.
    nombre = f"iglesias_prueba_{uuid.uuid4().hex[:12]}"
    # AUTOCOMMIT: CREATE/DROP DATABASE no pueden ir dentro de una transacción.
    motor_admin = create_engine(url_servidor, isolation_level="AUTOCOMMIT")
    try:
        conexion_fallo = False
        try:
            with motor_admin.connect() as conexion:
                conexion.execute(text(f'CREATE DATABASE "{nombre}"'))
        except DBAPIError:
            conexion_fallo = True
        if conexion_fallo:
            # Se avisa FUERA del except para que pytest no muestre el error original,
            # que podría incluir datos de conexión.
            pytest.fail(MENSAJE_SIN_CONEXION, pytrace=False)
        try:
            yield url_servidor.set(database=nombre)
        finally:
            with motor_admin.connect() as conexion:
                # WITH (FORCE) cierra conexiones que hayan quedado abiertas.
                conexion.execute(text(f'DROP DATABASE IF EXISTS "{nombre}" WITH (FORCE)'))
    finally:
        motor_admin.dispose()


def _config_alembic(url: URL) -> Config:
    """Configuración de Alembic que apunta a la base temporal (la URL no se escribe en texto)."""
    config = Config(str(RUTA_ALEMBIC_INI))
    config.attributes["url"] = url
    return config


@pytest.fixture
def base_temporal(url_servidor: URL) -> Iterator[URL]:
    """Una base temporal vacía para cada prueba que la pida."""
    with _base_temporal(url_servidor) as url:
        yield url


@pytest.fixture(scope="module")
def motor_migrado(url_servidor: URL) -> Iterator:
    """Una base temporal con la migración ya aplicada, compartida por todo este archivo."""
    with _base_temporal(url_servidor) as url:
        command.upgrade(_config_alembic(url), "head")
        motor = create_engine(url)
        yield motor
        motor.dispose()


@pytest.fixture
def sesion(motor_migrado) -> Iterator[Session]:
    """Una sesión cuyos cambios se deshacen al terminar la prueba (no deja datos)."""
    conexion = motor_migrado.connect()
    transaccion = conexion.begin()
    sesion = Session(bind=conexion)
    try:
        yield sesion
    finally:
        sesion.close()
        # Deshace todo lo que hizo la prueba. Si un error de la base ya cerró la
        # transacción (pasa en las pruebas que esperan un IntegrityError), no hay nada que deshacer.
        if transaccion.is_active:
            transaccion.rollback()
        conexion.close()


def _crear_iglesia(sesion: Session) -> Iglesia:
    """Inserta una iglesia ficticia con nombre único y devuelve el objeto con su id."""
    iglesia = Iglesia(nombre=f"Iglesia de prueba {uuid.uuid4().hex[:8]}")
    sesion.add(iglesia)
    sesion.flush()  # envía el INSERT a la base para que se validen las restricciones
    return iglesia


def _nuevo_usuario(nombre_usuario: str, cargo: str, iglesia_id: int | None) -> Usuario:
    """Arma un usuario ficticio. El "hash" es un texto inventado, no una contraseña real."""
    return Usuario(
        nombre_usuario=nombre_usuario,
        contrasena_hash="hash-inventado-solo-para-pruebas",
        nombre_completo="Persona de Prueba",
        cargo=cargo,
        iglesia_id=iglesia_id,
    )


def test_upgrade_y_downgrade(base_temporal: URL) -> None:
    """`upgrade head` crea las tablas, `downgrade base` las quita y se puede volver a subir."""
    config = _config_alembic(base_temporal)
    motor = create_engine(base_temporal)
    try:
        command.upgrade(config, "head")
        assert {"iglesias", "usuarios"} <= set(inspect(motor).get_table_names())

        command.downgrade(config, "base")
        # Solo queda la tabla interna de Alembic que lleva la cuenta de las migraciones.
        assert set(inspect(motor).get_table_names()) == {"alembic_version"}

        command.upgrade(config, "head")
        assert {"iglesias", "usuarios"} <= set(inspect(motor).get_table_names())
    finally:
        motor.dispose()


def test_modelos_coinciden_con_la_migracion(motor_migrado) -> None:
    """Los modelos de Python y la migración describen exactamente las mismas tablas."""
    with motor_migrado.connect() as conexion:
        contexto = MigrationContext.configure(conexion, opts={"compare_type": True})
        diferencias = compare_metadata(contexto, Base.metadata)
    assert diferencias == []


def test_solo_se_guarda_el_hash_de_la_contrasena() -> None:
    """Existe `contrasena_hash` y no hay ninguna columna para la contraseña en texto."""
    columnas = Usuario.__table__.columns.keys()
    assert "contrasena_hash" in columnas
    assert "contrasena" not in columnas


def test_valores_por_defecto_de_un_usuario(sesion: Session) -> None:
    """Un usuario nuevo queda activo y con fecha de creación con zona horaria."""
    iglesia = _crear_iglesia(sesion)
    usuario = _nuevo_usuario("usuario.defecto", "pastor", iglesia.id)
    sesion.add(usuario)
    sesion.flush()
    sesion.refresh(usuario)  # vuelve a leer los valores que puso PostgreSQL
    assert usuario.activo is True
    assert usuario.creado_en.tzinfo is not None


@pytest.mark.parametrize("cargo", CARGOS)
def test_cada_cargo_de_la_lista_se_acepta(sesion: Session, cargo: str) -> None:
    """Los 13 cargos de la lista cerrada se pueden guardar (con la iglesia que les toca)."""
    # El presbítero va sin iglesia; los demás cargos llevan una.
    iglesia_id = None if cargo == "presbitero" else _crear_iglesia(sesion).id
    usuario = _nuevo_usuario(f"usuario.{cargo}", cargo, iglesia_id)
    sesion.add(usuario)
    sesion.flush()
    assert usuario.id is not None


def test_cargo_invalido_se_rechaza(sesion: Session) -> None:
    """Un cargo que no está en la lista cerrada falla por el CHECK ck_usuarios_cargo."""
    iglesia = _crear_iglesia(sesion)
    sesion.add(_nuevo_usuario("usuario.cargo.invalido", "jardinero", iglesia.id))
    with pytest.raises(IntegrityError, match="ck_usuarios_cargo"):
        sesion.flush()


@pytest.mark.parametrize("cargo", [cargo for cargo in CARGOS if cargo != "presbitero"])
def test_cargo_distinto_de_presbitero_sin_iglesia_se_rechaza(sesion: Session, cargo: str) -> None:
    """Solo el presbítero puede no tener iglesia; cualquier otro cargo sin iglesia falla."""
    sesion.add(_nuevo_usuario(f"sin.iglesia.{cargo}", cargo, None))
    with pytest.raises(IntegrityError, match="ck_usuarios_iglesia_segun_cargo"):
        sesion.flush()


def test_nombre_de_usuario_duplicado_en_otras_mayusculas_se_rechaza(sesion: Session) -> None:
    """"Maria.Lopez" y "maria.lopez" cuentan como el mismo usuario."""
    iglesia = _crear_iglesia(sesion)
    sesion.add(_nuevo_usuario("Maria.Lopez", "tesorero", iglesia.id))
    sesion.flush()  # el primero se guarda bien
    sesion.add(_nuevo_usuario("maria.lopez", "ujier", iglesia.id))
    with pytest.raises(IntegrityError, match="uq_usuarios_nombre_usuario_minusculas"):
        sesion.flush()


def test_nombre_de_iglesia_duplicado_se_rechaza(sesion: Session) -> None:
    """No puede haber dos iglesias con el mismo nombre."""
    sesion.add(Iglesia(nombre="Iglesia repetida de prueba"))
    sesion.flush()
    sesion.add(Iglesia(nombre="Iglesia repetida de prueba"))
    with pytest.raises(IntegrityError, match="uq_iglesias_nombre"):
        sesion.flush()


def test_borrar_una_iglesia_con_usuarios_falla(sesion: Session) -> None:
    """No se puede borrar una iglesia que todavía tiene usuarios (llave foránea RESTRICT)."""
    iglesia = _crear_iglesia(sesion)
    sesion.add(_nuevo_usuario("usuario.de.la.iglesia", "pastor", iglesia.id))
    sesion.flush()
    with pytest.raises(IntegrityError, match="fk_usuarios_iglesia_id"):
        sesion.execute(delete(Iglesia).where(Iglesia.id == iglesia.id))
