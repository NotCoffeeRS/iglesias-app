"""Punto de entrada: uvicorn app.main:app."""

from importlib import import_module
from pathlib import Path

from fastapi import FastAPI

from app import modulos


def registrar_routers(aplicacion: FastAPI) -> None:
    """Descubre app/modulos/*/rutas.py, incluso sin __init__.py en cada módulo.

    Cada archivo debe exponer un APIRouter llamado router. Los errores de importación
    se propagan para no arrancar con módulos faltantes silenciosamente.
    """
    for directorio in modulos.__path__:
        for archivo in sorted(Path(directorio).glob("*/rutas.py")):
            modulo = import_module(f"{modulos.__name__}.{archivo.parent.name}.rutas")
            aplicacion.include_router(modulo.router)


def crear_app() -> FastAPI:
    aplicacion = FastAPI(title="Iglesias App")
    registrar_routers(aplicacion)
    return aplicacion


app = crear_app()
