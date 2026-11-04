"""Modelo de la tabla `usuarios` (Issues #7, #9 y #4; decisiones D19 y D20).

Cada persona que entra a la aplicación tiene un usuario con un cargo (lista cerrada)
y, salvo el presbítero, una iglesia. Quién puede crear a quién (D19/D20) lo valida
el servidor en el Issue #9; aquí solo se guardan los datos y las reglas de integridad.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.modelos.utilidades import lista_sql

# Lista cerrada de cargos (AGENTS.md §9 y Issue #23 para el ujier). Si hay que
# agregar uno, se hace con una migración nueva que cambie el CHECK de abajo.
CARGOS = (
    "presbitero",
    "pastor",
    "esposa_pastor",
    "apoyo_pastor",
    "tesorero",
    "lider_red",
    "lider_celula",
    "lider_ministerio",
    "asistente",
    "diacono",
    "ministro",
    "encargado_area",
    "ujier",
)


class Usuario(Base):
    """Una cuenta de la aplicación (liderazgo del Presbiterio)."""

    __tablename__ = "usuarios"

    # Llave primaria numérica (misma idea que en `iglesias`).
    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)

    # Nombre con el que se inicia sesión (#7). Es único sin distinguir mayúsculas
    # (índice más abajo): "Maria" y "maria" cuentan como el mismo usuario.
    nombre_usuario: Mapped[str] = mapped_column(String(60), nullable=False)

    # Solo se guarda el HASH de la contraseña, nunca el texto (AGENTS.md §4.9).
    contrasena_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Nombre de la persona, para mostrarlo en pantalla.
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)

    # Cargo del usuario; solo acepta los valores de CARGOS (CHECK más abajo).
    cargo: Mapped[str] = mapped_column(String(20), nullable=False)

    # Iglesia a la que pertenece. NULL solo para el presbítero, que ve todas (#9).
    # RESTRICT: no se puede borrar una iglesia que todavía tiene usuarios.
    iglesia_id: Mapped[int | None] = mapped_column(
        ForeignKey("iglesias.id", ondelete="RESTRICT", name="fk_usuarios_iglesia_id")
    )

    # Los usuarios no se borran: se desactivan (plan de permisos del Issue #10).
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    # Fecha y hora de creación, con zona horaria (AGENTS.md §2).
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        # El cargo debe ser uno de la lista cerrada.
        CheckConstraint(f"cargo IN ({lista_sql(CARGOS)})", name="ck_usuarios_cargo"),
        # Solo el presbítero puede no tener iglesia; los demás cargos siempre la tienen.
        CheckConstraint(
            "cargo = 'presbitero' OR iglesia_id IS NOT NULL",
            name="ck_usuarios_iglesia_segun_cargo",
        ),
        # Nombre de usuario único SIN distinguir mayúsculas: se indexa lower(nombre_usuario).
        # Nota para el login (#7): hay que buscar comparando también en minúsculas.
        Index("uq_usuarios_nombre_usuario_minusculas", func.lower(nombre_usuario), unique=True),
    )
