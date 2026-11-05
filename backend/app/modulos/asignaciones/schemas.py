"""Solo identificadores para asignar; nombres y estado mínimos para el selector."""

from pydantic import BaseModel, ConfigDict, Field


class AsignacionEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grupo_id: int = Field(gt=0)
    miembro_id: int = Field(gt=0)


class AsignacionRespuesta(BaseModel):
    grupo_id: int
    miembro_id: int


class MiembroOpcion(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    estado: str


class GrupoOpcion(BaseModel):
    id: int
    nombre: str
    tipo: str
    iglesia_id: int
    iglesia_nombre: str
    activo: bool
