"""Modelos de la base de datos (un archivo por módulo, Issue #4).

Importar aquí cada modelo hace que SQLAlchemy y Alembic conozcan todas las tablas
con solo hacer `import app.modelos`.
"""

from app.modelos.iglesias import Iglesia
from app.modelos.sedes import Horario, RedSocial, Sede
from app.modelos.usuarios import CARGOS, Usuario

__all__ = [
    "CARGOS",
    "Horario",
    "Iglesia",
    "RedSocial",
    "Sede",
    "Usuario",
]
