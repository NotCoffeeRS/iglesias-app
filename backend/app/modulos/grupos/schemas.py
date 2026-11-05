"""Contrato de grupos (#20), el mismo que usa la pantalla `frontend/src/api/grupos.ts`.

El líder y el asistente son miembros (D21 y el modelo `grupos.lider_miembro_id`).
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modelos.listas import TIPOS_GRUPO


class GrupoEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=150)
    tipo: str
    iglesia_id: int = Field(gt=0)
    lider_id: int = Field(gt=0)
    asistente_id: int | None = Field(default=None, gt=0)

    @field_validator("nombre")
    @classmethod
    def nombre_con_texto(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("Escribe el nombre")
        return valor

    @field_validator("tipo")
    @classmethod
    def tipo_conocido(cls, valor: str) -> str:
        if valor not in TIPOS_GRUPO:
            raise ValueError("Tipo no válido")
        return valor


class GrupoRespuesta(BaseModel):
    id: int
    nombre: str
    tipo: str
    iglesia_id: int
    lider_id: int
    asistente_id: int | None


class GrupoResumen(BaseModel):
    """Lo que necesita una lista: nombres en lugar de números."""

    id: int
    nombre: str
    tipo: str
    iglesia_id: int
    iglesia_nombre: str
    lider_nombre: str | None
    asistente_nombre: str | None
