"""Modelo `asistencias` (Issue #23, decisión D16).

El líder de célula marca quién de su célula asistió; el ujier marca quién faltó de quienes
no tienen célula. Cada fila es la marca de UNA persona en UN servicio de UN día.
"""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.modelos.listas import TIPOS_SERVICIO
from app.modelos.utilidades import lista_sql


class Asistencia(Base):
    """La asistencia (o falta) de un miembro a un servicio en una fecha."""

    __tablename__ = "asistencias"

    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)

    miembro_id: Mapped[int] = mapped_column(
        ForeignKey("miembros.id", ondelete="RESTRICT", name="fk_asistencias_miembro_id"),
        nullable=False,
    )

    fecha: Mapped[date] = mapped_column(Date, nullable=False)

    # Servicio al que corresponde (domingo, entre semana u otro de la lista de 8).
    tipo_servicio: Mapped[str] = mapped_column(String(20), nullable=False)

    # Verdadero = asistió; falso = faltó.
    presente: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Quién hizo la marca (el líder o el ujier): sirve para saber quién la capturó.
    registrado_por: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT", name="fk_asistencias_registrado_por"),
        nullable=False,
    )
    registrado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            f"tipo_servicio IN ({lista_sql(TIPOS_SERVICIO)})", name="ck_asistencias_tipo_servicio"
        ),
        # Una persona no se marca dos veces el mismo día y servicio (Issue #23).
        UniqueConstraint(
            "miembro_id", "fecha", "tipo_servicio", name="uq_asistencias_miembro_fecha_servicio"
        ),
    )
