"""Punto de entrada: uvicorn app.main:app."""

from importlib import import_module
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import modulos
from app.config import cargar_configuracion


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
    configuracion = cargar_configuracion()
    aplicacion.add_middleware(
        CORSMiddleware,
        allow_origins=configuracion.cors_origins,
        # El cliente actual usa Authorization: Bearer, sin cookies entre orígenes.
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    registrar_routers(aplicacion)
    return aplicacion


app = crear_app()
