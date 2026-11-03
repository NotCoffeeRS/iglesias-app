"""Modelo `comunicados` (Issue #33).

Un comunicado es de una iglesia o de todo el Presbiterio (cuando `iglesia_id` está vacío) y
tiene una fecha de vigencia: "solo se ven los vigentes" se resuelve en la consulta con
`vigente_hasta >= hoy`.
"""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Comunicado(Base):
    """Un aviso o anuncio para los miembros del liderazgo."""

    __tablename__ = "comunicados"

    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)

    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)

    # Iglesia destino. VACÍO = comunicado de todo el Presbiterio (#33).
    iglesia_id: Mapped[int | None] = mapped_column(
        ForeignKey("iglesias.id", ondelete="RESTRICT", name="fk_comunicados_iglesia_id")
    )

    # Cuándo se publicó (RF-07: "indicar fecha de publicación").
    publicado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Último día en que se muestra (#33: "con fecha de vigencia"; obligatoria es propuesta).
    vigente_hasta: Mapped[date] = mapped_column(Date, nullable=False)

    # Quién lo publicó.
    creado_por: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT", name="fk_comunicados_creado_por"),
        nullable=False,
    )

    __table_args__ = (
        # La vigencia no puede terminar antes del día de publicación. Se usa la zona de
        # Mérida con una zona fija para que la regla no cambie según la sesión (AGENTS.md §2).
        CheckConstraint(
            "vigente_hasta >= (publicado_en AT TIME ZONE 'America/Merida')::date",
            name="ck_comunicados_vigencia",
        ),
    )
