"""Modelo `eventos` (Issue #32).

Un evento es de una iglesia o de todo el Presbiterio (cuando `iglesia_id` está vacío).
Costo, inscripción y recordatorios NO se modelan: el Issue #32 dice que no se implementen.
"""

from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, Identity, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Evento(Base):
    """Un evento religioso o administrativo."""

    __tablename__ = "eventos"

    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)

    # Título del evento. El Issue #32 no lo menciona pero RF-04 lo pide (propuesta).
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)

    # Fecha y hora van separadas (como las pide #32): son hora local de Mérida, sin zona.
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora: Mapped[time] = mapped_column(Time, nullable=False)

    # Iglesia del evento. VACÍO = evento de todo el Presbiterio (#32).
    iglesia_id: Mapped[int | None] = mapped_column(
        ForeignKey("iglesias.id", ondelete="RESTRICT", name="fk_eventos_iglesia_id")
    )

    # Lugar (RF-04, propuesta) y descripción (#32).
    lugar: Mapped[str | None] = mapped_column(String(200))
    descripcion: Mapped[str | None] = mapped_column(Text)

    # Quién creó el evento.
    creado_por: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT", name="fk_eventos_creado_por"),
        nullable=False,
    )

    # Un evento no se borra: se cancela (RF-04, propuesta). Cancelado = cancelado_en NOT NULL.
    cancelado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
