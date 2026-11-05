"""Configuración leída de las variables de entorno del proceso."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Configuracion:
    database_url: str
    cors_origins: tuple[str, ...]


def cargar_configuracion() -> Configuracion:
    origenes = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    # Permite arrancar y probar /salud sin una base externa ni crear archivos.
    return Configuracion(
        database_url=os.environ.get("DATABASE_URL", "sqlite+pysqlite:///:memory:"),
        cors_origins=tuple(origen.strip() for origen in origenes.split(",") if origen.strip()),
    )


configuracion = cargar_configuracion()
