"""Modelos de la base de datos (un archivo por módulo, Issue #4).

Importar aquí cada modelo hace que SQLAlchemy y Alembic conozcan todas las tablas
con solo hacer `import app.modelos`. El segundo PR del Issue #4 agregará el resto.
"""

from app.modelos.iglesias import Iglesia
from app.modelos.usuarios import CARGOS, Usuario

__all__ = ["CARGOS", "Iglesia", "Usuario"]
