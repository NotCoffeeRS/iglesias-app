"""Modelos de la base de datos (un archivo por módulo, Issue #4).

Importar aquí cada modelo hace que SQLAlchemy y Alembic conozcan todas las tablas
con solo hacer `import app.modelos`.
"""

from app.modelos.asistencia import Asistencia
from app.modelos.comunicados import Comunicado
from app.modelos.eventos import Evento
from app.modelos.gastos import Gasto
from app.modelos.grupos import Grupo, GrupoMiembro
from app.modelos.iglesias import Iglesia
from app.modelos.ingresos import Ingreso
from app.modelos.miembros import Menor, Miembro, Tutor
from app.modelos.sedes import Horario, RedSocial, Sede
from app.modelos.usuarios import CARGOS, Usuario

__all__ = [
    "CARGOS",
    "Asistencia",
    "Comunicado",
    "Evento",
    "Gasto",
    "Grupo",
    "GrupoMiembro",
    "Horario",
    "Iglesia",
    "Ingreso",
    "Menor",
    "Miembro",
    "RedSocial",
    "Sede",
    "Tutor",
    "Usuario",
]
