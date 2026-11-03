"""Modelos `grupos` y `grupo_miembros` (Issues #4, #20 y #22).

Un grupo puede ser una red, una célula, un ministerio, una escuela o un área. Tiene un
líder y, opcionalmente, un asistente (o segundo al mando). Los miembros se asignan a los
grupos en `grupo_miembros`.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.modelos.listas import TIPOS_GRUPO
from app.modelos.utilidades import lista_sql


class Grupo(Base):
    """Un grupo de trabajo o de reunión de una iglesia."""

    __tablename__ = "grupos"

    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)
    iglesia_id: Mapped[int] = mapped_column(
        ForeignKey("iglesias.id", ondelete="RESTRICT", name="fk_grupos_iglesia_id"),
        nullable=False,
    )

    # Tipo de grupo (lista cerrada de 5) y nombre.
    tipo: Mapped[str] = mapped_column(String(12), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)

    # Líder obligatorio. Es un USUARIO (con cuenta) porque marca asistencia en la app
    # (Issue #23); por eso el "área" de un usuario es el grupo que lidera, no una columna
    # aparte en `usuarios`. Propuesta pendiente de confirmar con Marcos.
    lider_usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT", name="fk_grupos_lider_usuario_id"),
        nullable=False,
    )

    # Asistente o segundo al mando (opcional, Issue #20).
    asistente_usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT", name="fk_grupos_asistente_usuario_id")
    )

    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    __table_args__ = (
        CheckConstraint(f"tipo IN ({lista_sql(TIPOS_GRUPO)})", name="ck_grupos_tipo"),
        # El líder y el asistente no pueden ser la misma persona.
        CheckConstraint(
            "asistente_usuario_id IS NULL OR lider_usuario_id <> asistente_usuario_id",
            name="ck_grupos_lider_distinto_asistente",
        ),
        # No se repite el nombre de un grupo del mismo tipo en la misma iglesia.
        UniqueConstraint("iglesia_id", "tipo", "nombre", name="uq_grupos_iglesia_tipo_nombre"),
        # Restricción técnica: permite que `grupo_miembros` verifique el tipo con una llave
        # foránea compuesta (grupo_id, tipo_grupo).
        UniqueConstraint("id", "tipo", name="uq_grupos_id_tipo"),
    )


class GrupoMiembro(Base):
    """Un miembro dentro de un grupo (Issue #22)."""

    __tablename__ = "grupo_miembros"

    grupo_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    miembro_id: Mapped[int] = mapped_column(
        ForeignKey("miembros.id", ondelete="RESTRICT", name="fk_grupo_miembros_miembro_id"),
        primary_key=True,
    )

    # Copia del tipo del grupo. Una llave foránea compuesta obliga a que coincida con el
    # tipo real del grupo; se necesita para limitar a UNA célula por miembro (más abajo).
    tipo_grupo: Mapped[str] = mapped_column(String(12), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["grupo_id", "tipo_grupo"],
            ["grupos.id", "grupos.tipo"],
            ondelete="RESTRICT",
            name="fk_grupo_miembros_grupo_tipo",
        ),
        # Un miembro solo puede estar en UNA célula (suposición pendiente, Issue #22), pero
        # sí en varios ministerios. Si la clienta dice que puede estar en varias células,
        # basta quitar este índice con una migración.
        Index(
            "uq_grupo_miembros_una_celula",
            "miembro_id",
            unique=True,
            postgresql_where=text("tipo_grupo = 'celula'"),
        ),
    )
