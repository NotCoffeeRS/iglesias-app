"""Pruebas del esqueleto sin conexiones a bases externas."""

import importlib
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app import db, modulos
from app.config import cargar_configuracion
from app.main import app, crear_app


def test_salud_responde_200():
    with TestClient(app) as cliente:
        respuesta = cliente.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}


def test_descubre_modulo_nuevo_sin_editar_main(tmp_path, monkeypatch):
    nuevo = tmp_path / "ejemplo_dinamico"
    nuevo.mkdir()
    (nuevo / "rutas.py").write_text(
        'from fastapi import APIRouter\n'
        'router = APIRouter()\n'
        '@router.get("/ejemplo-dinamico")\n'
        'def ejemplo():\n'
        '    return {"descubierto": True}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(modulos, "__path__", [*modulos.__path__, str(tmp_path)])
    importlib.invalidate_caches()
    try:
        with TestClient(crear_app()) as cliente:
            respuesta = cliente.get("/ejemplo-dinamico")
            assert cliente.get("/salud").status_code == 200
        assert respuesta.status_code == 200
        assert respuesta.json() == {"descubierto": True}
    finally:
        sys.modules.pop("app.modulos.ejemplo_dinamico.rutas", None)
        sys.modules.pop("app.modulos.ejemplo_dinamico", None)


def test_configuracion_lee_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///ejemplo.db")
    assert cargar_configuracion().database_url == "sqlite+pysqlite:///ejemplo.db"


def test_db_usa_database_url_del_entorno(monkeypatch):
    # Un proceso nuevo comprueba la configuración al importar sin alterar otros tests.
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///configuracion_prueba.db")
    resultado = subprocess.run(
        [
            sys.executable,
            "-c",
            "from app.db import Base, engine; "
            "from sqlalchemy.orm import DeclarativeBase; "
            "assert issubclass(Base, DeclarativeBase); "
            "assert str(engine.url) == 'sqlite+pysqlite:///configuracion_prueba.db'; "
            "engine.dispose()",
        ],
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, resultado.stderr


@pytest.mark.parametrize("fallar", [False, True])
def test_get_db_libera_sesion(monkeypatch, fallar):
    motor = create_engine("sqlite+pysqlite:///:memory:")
    sesion = Session(motor)
    monkeypatch.setattr(db, "SessionLocal", lambda: sesion)
    dependencia = db.get_db()
    try:
        assert next(dependencia) is sesion
        assert sesion.scalar(text("SELECT 1")) == 1
        assert sesion.in_transaction()
        if fallar:
            with pytest.raises(ValueError, match="fallo de prueba"):
                dependencia.throw(ValueError("fallo de prueba"))
        else:
            with pytest.raises(StopIteration):
                next(dependencia)
        assert not sesion.in_transaction()
    finally:
        dependencia.close()
        motor.dispose()
