"""Funciones de apoyo compartidas por los modelos, Alembic y las pruebas."""

import os
from pathlib import Path

# Ruta de backend/.env. Este archivo vive en backend/app/modelos/, así que
# subimos dos carpetas (modelos -> app -> backend) para llegar a backend/.
RUTA_ENV = Path(__file__).resolve().parents[2] / ".env"


def lista_sql(valores: tuple[str, ...]) -> str:
    """Convierte ('a', 'b') en "'a', 'b'" para usarlo dentro de un CHECK ... IN (...).

    Así la lista de valores permitidos se escribe una sola vez en Python y se
    reutiliza en el modelo, sin copiar y pegar texto SQL a mano.
    """
    return ", ".join(f"'{valor}'" for valor in valores)


def _leer_variable_de_env(nombre: str) -> str | None:
    """Busca `nombre=valor` dentro de backend/.env sin cargar librerías extra."""
    if not RUTA_ENV.is_file():
        return None
    for linea in RUTA_ENV.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        # Se ignoran líneas vacías, comentarios y líneas sin signo '='.
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        if clave.strip() == nombre:
            # Se quitan espacios y comillas opcionales alrededor del valor.
            return valor.strip().strip("'\"")
    return None


def obtener_url_base_datos() -> str | None:
    """Devuelve DATABASE_URL (del entorno o de backend/.env), o None si no existe.

    Si la URL empieza con "postgresql://" se cambia a "postgresql+psycopg://",
    que es el controlador (psycopg 3) que usa este proyecto (pyproject.toml).
    Nunca se imprime la URL: puede contener la contraseña.
    """
    url = os.environ.get("DATABASE_URL") or _leer_variable_de_env("DATABASE_URL")
    if not url:
        return None
    for prefijo in ("postgresql://", "postgres://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg://" + url[len(prefijo):]
    return url
