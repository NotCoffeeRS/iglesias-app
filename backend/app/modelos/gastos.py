"""Modelo `gastos` (Issues #4 y #27, decisión D18). Módulo crítico.

Cada gasto tiene una categoría de una lista cerrada de 8. Igual que los ingresos, un gasto
nunca se borra: se anula con motivo. El flujo de autorización de gastos (D18) está por
confirmar, así que todavía no hay columnas para eso.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.modelos.listas import CATEGORIAS_GASTO
from app.modelos.utilidades import lista_sql


class Gasto(Base):
    """Una cantidad de dinero gastada por una iglesia."""

    __tablename__ = "gastos"

    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)

    iglesia_id: Mapped[int] = mapped_column(
        ForeignKey("iglesias.id", ondelete="RESTRICT", name="fk_gastos_iglesia_id"),
        nullable=False,
    )

    fecha: Mapped[date] = mapped_column(Date, nullable=False)

    # Una de las 8 categorías (luz, agua, renta, mantenimiento, ...).
    categoria: Mapped[str] = mapped_column(String(24), nullable=False)

    # Dinero: NUMERIC(12,2) y siempre mayor que 0.
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Nota libre sobre el gasto (Issue #27).
    nota: Mapped[str | None] = mapped_column(Text)

    # Quién capturó el gasto (un usuario).
    registrado_por: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT", name="fk_gastos_registrado_por"),
        nullable=False,
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # --- Anulación (no se borra): "anulado" significa anulado_en IS NOT NULL ---
    anulado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    anulado_motivo: Mapped[str | None] = mapped_column(Text)
    anulado_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT", name="fk_gastos_anulado_por")
    )

    __table_args__ = (
        CheckConstraint(
            f"categoria IN ({lista_sql(CATEGORIAS_GASTO)})", name="ck_gastos_categoria"
        ),
        CheckConstraint("monto > 0", name="ck_gastos_monto_positivo"),
        # Anular exige motivo (no vacío), fecha y quién; o no hay anulación (nada a medias).
        CheckConstraint(
            "(anulado_en IS NULL AND anulado_motivo IS NULL AND anulado_por IS NULL) "
            "OR (anulado_en IS NOT NULL AND btrim(coalesce(anulado_motivo, '')) <> '' "
            "AND anulado_por IS NOT NULL)",
            name="ck_gastos_anulacion",
        ),
    )
