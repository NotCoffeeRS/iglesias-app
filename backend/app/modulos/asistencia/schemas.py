"""Contrato de asistencia (#23), el mismo que usa la pantalla `frontend/src/api/asistencia.ts`.

Una "hoja" es una lista de personas que quien usa la app puede marcar:
- `modo = "asistencias"`: la célula de un líder; lo marcado significa que la persona ASISTIÓ.
- `modo = "faltas"`: los miembros sin célula del ujier; lo marcado significa que la persona FALTÓ.
"""

from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modelos.listas import TIPOS_SERVICIO_ASISTENCIA


def hoy() -> date:
    """La fecha de hoy en UTC: nunca va atrás de la de Mérida, así que no rechaza el día de hoy."""
    return datetime.now(timezone.utc).date()


def _servicio_conocido(valor: str) -> str:
    if valor not in TIPOS_SERVICIO_ASISTENCIA:
        raise ValueError("Culto no válido")
    return valor


def _fecha_pasada(valor: date) -> date:
    if valor > hoy():
        raise ValueError("La fecha no puede ser futura")
    return valor


class PersonaHoja(BaseModel):
    miembro_id: int
    nombre: str
    marcado: bool


class HojaRespuesta(BaseModel):
    hoja: str
    modo: Literal["asistencias", "faltas"]
    titulo: str
    guardada: bool
    personas: list[PersonaHoja]


class GuardarHoja(BaseModel):
    """Reemplaza las marcas de una hoja para una fecha y un culto."""

    model_config = ConfigDict(extra="forbid")

    fecha: date
    servicio: str
    hoja: str = Field(min_length=1, max_length=40)
    marcados: list[int] = Field(max_length=2000)

    _fecha = field_validator("fecha")(_fecha_pasada)
    _servicio = field_validator("servicio")(_servicio_conocido)
