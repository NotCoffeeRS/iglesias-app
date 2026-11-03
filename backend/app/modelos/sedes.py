"""Modelos `sedes`, `redes_sociales` y `horarios` (Issues #12, #14 y #4; decisiones D8 y D10).

Una iglesia tiene una o más sedes (la 3ra de Mérida tiene dos: Madero y Kanasín), varias
redes sociales y los horarios de cada sede.
"""

from datetime import time

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.modelos.listas import DIAS_SEMANA, TIPOS_RED_SOCIAL, TIPOS_SERVICIO
from app.modelos.utilidades import lista_sql


class Sede(Base):
    """Un lugar físico donde se reúne una iglesia."""

    __tablename__ = "sedes"

    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)

    # RESTRICT: no se puede borrar una iglesia que todavía tiene sedes.
    iglesia_id: Mapped[int] = mapped_column(
        ForeignKey("iglesias.id", ondelete="RESTRICT", name="fk_sedes_iglesia_id"),
        nullable=False,
    )

    # Nombre de la sede (por ejemplo "Madero" o "Kanasín").
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)

    # Dirección escrita y enlace de Google Maps (decisión D10: no hay mapa propio).
    direccion: Mapped[str] = mapped_column(Text, nullable=False)
    enlace_maps: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        # Una iglesia no puede tener dos sedes con el mismo nombre.
        UniqueConstraint("iglesia_id", "nombre", name="uq_sedes_iglesia_nombre"),
    )


class RedSocial(Base):
    """Una red social de la iglesia: propia o relacionada (Issue #12)."""

    __tablename__ = "redes_sociales"

    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)
    iglesia_id: Mapped[int] = mapped_column(
        ForeignKey("iglesias.id", ondelete="RESTRICT", name="fk_redes_sociales_iglesia_id"),
        nullable=False,
    )

    # Nombre visible ("Facebook", "Instagram"...) y el enlace.
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)

    # "propia" (de esta iglesia) o "relacionada" (de otra iglesia o ministerio amigo).
    tipo: Mapped[str] = mapped_column(String(12), nullable=False)

    __table_args__ = (
        CheckConstraint(f"tipo IN ({lista_sql(TIPOS_RED_SOCIAL)})", name="ck_redes_sociales_tipo"),
    )


class Horario(Base):
    """Un horario de reunión de una sede (Issue #14)."""

    __tablename__ = "horarios"

    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)
    sede_id: Mapped[int] = mapped_column(
        ForeignKey("sedes.id", ondelete="RESTRICT", name="fk_horarios_sede_id"),
        nullable=False,
    )

    # Tipo de servicio (lista cerrada de 8) y día de la semana (lista cerrada de 7).
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    dia: Mapped[str] = mapped_column(String(10), nullable=False)

    # Hora de inicio y, opcionalmente, de fin. Son horas locales de la sede (sin zona).
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time | None] = mapped_column(Time)

    descripcion: Mapped[str | None] = mapped_column(String(200))

    __table_args__ = (
        CheckConstraint(f"tipo IN ({lista_sql(TIPOS_SERVICIO)})", name="ck_horarios_tipo"),
        CheckConstraint(f"dia IN ({lista_sql(DIAS_SEMANA)})", name="ck_horarios_dia"),
        # Si hay hora de fin, debe ser posterior a la de inicio.
        CheckConstraint(
            "hora_fin IS NULL OR hora_fin > hora_inicio", name="ck_horarios_hora_fin"
        ),
        # Evita duplicar exactamente el mismo horario. OJO: NO hay unicidad por (sede, tipo),
        # porque una sede puede tener varios horarios del mismo tipo (Issue #14).
        UniqueConstraint(
            "sede_id", "tipo", "dia", "hora_inicio", name="uq_horarios_sede_tipo_dia_hora"
        ),
    )
