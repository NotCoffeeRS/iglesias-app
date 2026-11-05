"""Contrato JSON de comunicados; el frontend lo espera en frontend/src/api/comunicados.ts."""

from datetime import date, datetime
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
    "contenido": "Escribe el contenido del comunicado (hasta 5000 letras).",
    "vigente_hasta": "Escribe una fecha de vigencia válida.",
}


class ComunicadoEntrada(BaseModel):
    """Lo que se envía al publicar o editar. `iglesia_id` vacío = todo el Presbiterio."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    titulo: str = Field(min_length=1, max_length=150)
    contenido: str = Field(min_length=1, max_length=5000)
    iglesia_id: int | None = None
    vigente_hasta: date

    # El cliente muestra estos textos tal cual: así salen en español y no como los de Pydantic.
    @field_validator("titulo", "contenido", "vigente_hasta", mode="wrap")
    @classmethod
    def mensaje_en_espanol(
        cls, valor: Any, manejador: ValidatorFunctionWrapHandler, info: ValidationInfo
    ) -> Any:
        try:
            return manejador(valor)
        except ValidationError:
            raise PydanticCustomError("dato_invalido", _MENSAJES[info.field_name]) from None


class ComunicadoSalida(BaseModel):
    id: int
    titulo: str
    contenido: str
    iglesia_id: int | None
    iglesia_nombre: str | None
    publicado_en: datetime
    vigente_hasta: date
    vigente: bool
