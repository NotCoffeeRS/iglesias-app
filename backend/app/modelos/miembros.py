"""Modelos `miembros`, `menores` y `tutores` (Issues #17, #19 y #4; decisiones D14 y D15).

Los miembros nunca se borran: se pasan a estado `inactivo`. Los menores (4 a 17 años) se
guardan aparte, con sus tutores.
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
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.modelos.listas import ESTADOS_CIVILES, ESTADOS_MIEMBRO, SEXOS
from app.modelos.utilidades import lista_sql


class Miembro(Base):
    """Una persona registrada en la congregación (Issue #17)."""

    __tablename__ = "miembros"

    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)

    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(20))
    correo: Mapped[str | None] = mapped_column(String(254))
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)
    direccion: Mapped[str | None] = mapped_column(Text)

    # Estado civil (lista cerrada, opcional). OJO: no hay columnas de familia (Issue #17).
    estado_civil: Mapped[str | None] = mapped_column(String(12))

    fecha_bautizo: Mapped[date | None] = mapped_column(Date)

    # Desde cuándo forma parte de la congregación (D14). Puede quedar vacía en un visitante.
    fecha_ingreso: Mapped[date | None] = mapped_column(Date)

    iglesia_id: Mapped[int] = mapped_column(
        ForeignKey("iglesias.id", ondelete="RESTRICT", name="fk_miembros_iglesia_id"),
        nullable=False,
    )

    # Uno de los 6 estados. "inactivo" reemplaza al borrado: los miembros no se eliminan.
    estado: Mapped[str] = mapped_column(String(24), nullable=False)

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(f"estado IN ({lista_sql(ESTADOS_MIEMBRO)})", name="ck_miembros_estado"),
        CheckConstraint(
            f"estado_civil IS NULL OR estado_civil IN ({lista_sql(ESTADOS_CIVILES)})",
            name="ck_miembros_estado_civil",
        ),
    )


class Menor(Base):
    """Un niño, niña o adolescente de 4 a 17 años (Issue #19, decisión D15).

    La categoría (niño, niña o adolescente) NO se guarda: se calcula con la fecha de
    nacimiento y el sexo (Issue #19: "no se captura a mano"). La regla "de 4 a 17 años"
    depende de la fecha de hoy, así que no puede ser un CHECK y la valida el servicio.
    """

    __tablename__ = "menores"

    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)
    iglesia_id: Mapped[int] = mapped_column(
        ForeignKey("iglesias.id", ondelete="RESTRICT", name="fk_menores_iglesia_id"),
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)
    sexo: Mapped[str] = mapped_column(String(10), nullable=False)
    direccion: Mapped[str | None] = mapped_column(Text)

    # Igual que los miembros, un menor no se borra: se desactiva.
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    __table_args__ = (CheckConstraint(f"sexo IN ({lista_sql(SEXOS)})", name="ck_menores_sexo"),)


class Tutor(Base):
    """Un tutor de un menor, con nombre y teléfono (Issue #19)."""

    __tablename__ = "tutores"

    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)
    menor_id: Mapped[int] = mapped_column(
        ForeignKey("menores.id", ondelete="RESTRICT", name="fk_tutores_menor_id"),
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)

    # Obligatorio: el Issue #19 pide "tutores (nombre y teléfono)".
    telefono: Mapped[str] = mapped_column(String(20), nullable=False)
    # "Al menos un tutor por menor" no se puede forzar con una restricción simple:
    # lo valida el servicio del Issue #19.
