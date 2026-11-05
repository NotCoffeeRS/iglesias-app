"""Contrato JSON de eventos; el frontend lo espera en frontend/src/api/eventos.ts (PR 59)."""

from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventoEntrada(BaseModel):
    """Lo que se envía al crear o editar un evento. `iglesia_id` vacío = todo el Presbiterio."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    titulo: str = Field(min_length=1, max_length=150)
    fecha: date
    hora: time
    iglesia_id: int | None = None
    lugar: str | None = Field(default=None, max_length=200)
    descripcion: str | None = None

    @field_validator("hora")
    @classmethod
    def hora_sin_zona(cls, valor: time) -> time:
        # La columna guarda hora local de Mérida, sin zona.
        if valor.tzinfo is not None:
            raise ValueError("La hora va sin zona horaria, por ejemplo 19:30.")
        return valor

    @field_validator("lugar", "descripcion")
    @classmethod
    def vacio_es_nulo(cls, valor: str | None) -> str | None:
        return valor or None


class EventoSalida(BaseModel):
    id: int
    titulo: str
    fecha: date
    hora: time
    iglesia_id: int | None
    iglesia_nombre: str | None
    lugar: str | None
    descripcion: str | None
    cancelado: bool
