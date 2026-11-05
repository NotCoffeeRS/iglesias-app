"""Contrato JSON de eventos; el frontend lo espera en frontend/src/api/eventos.ts (PR 59)."""

from datetime import date, time
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    field_validator,
)
from pydantic_core import PydanticCustomError

_MENSAJES = {
    "titulo": "Escribe un título de 1 a 150 letras.",
    "fecha": "Escribe una fecha válida.",
    "hora": "Escribe una hora válida, sin zona horaria, como 19:30.",
    "lugar": "El lugar admite hasta 200 letras.",
    "descripcion": "La descripción admite hasta 5000 letras.",
}


class EventoEntrada(BaseModel):
    """Lo que se envía al crear o editar un evento. `iglesia_id` vacío = todo el Presbiterio."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    titulo: str = Field(min_length=1, max_length=150)
    fecha: date
    hora: time
    iglesia_id: int | None = None
    lugar: str | None = Field(default=None, max_length=200)
    descripcion: str | None = Field(default=None, max_length=5000)

    @field_validator("hora")
    @classmethod
    def hora_sin_zona(cls, valor: time) -> time:
        # La columna guarda hora local de Mérida, sin zona.
        if valor.tzinfo is not None:
            raise PydanticCustomError("hora_invalida", _MENSAJES["hora"])
        return valor

    @field_validator("lugar", "descripcion")
    @classmethod
    def vacio_es_nulo(cls, valor: str | None) -> str | None:
        return valor or None

    # Va al final para envolver a los demás: el cliente muestra estos textos tal cual, así que
    # los errores de formato, vacío y largo salen en español y no como los de Pydantic.
    @field_validator("titulo", "fecha", "hora", "lugar", "descripcion", mode="wrap")
    @classmethod
    def mensaje_en_espanol(
        cls, valor: Any, manejador: ValidatorFunctionWrapHandler, info: ValidationInfo
    ) -> Any:
        try:
            return manejador(valor)
        except ValidationError:
            raise PydanticCustomError("dato_invalido", _MENSAJES[info.field_name]) from None


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
