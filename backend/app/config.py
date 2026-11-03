"""Configuración leída de las variables de entorno del proceso."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Configuracion:
    database_url: str


def cargar_configuracion() -> Configuracion:
    # Permite arrancar y probar /salud sin una base externa ni crear archivos.
    return Configuracion(
        database_url=os.environ.get("DATABASE_URL", "sqlite+pysqlite:///:memory:"),
    )


configuracion = cargar_configuracion()
