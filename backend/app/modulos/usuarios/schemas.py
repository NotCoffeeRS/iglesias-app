"""Contrato de cuentas del frontend; el vínculo de área sigue pendiente de Marcos."""

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from app.modelos.usuarios import CARGOS


class DatosCuenta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre_completo: str = Field(min_length=1, max_length=150)
    cargo: str
    iglesia_id: int | None = Field(default=None, gt=0)

    @field_validator("cargo")
    @classmethod
    def cargo_conocido(cls, valor: str) -> str:
        if valor not in CARGOS:
            raise ValueError("Cargo no válido")
        return valor


class UsuarioNuevo(DatosCuenta):
    nombre_usuario: str = Field(min_length=1, max_length=60)
    contrasena: SecretStr = Field(min_length=1)


class UsuarioCambios(DatosCuenta):
    activo: bool


class UsuarioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre_usuario: str
    nombre_completo: str
    cargo: str
    iglesia_id: int | None
    activo: bool


class UsuarioResumen(UsuarioRespuesta):
    iglesia_nombre: str | None
