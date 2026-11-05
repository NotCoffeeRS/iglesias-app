"""Modelo `ingresos` (Issues #4 y #25, decisión D17). Módulo crítico.

Se registran CANTIDADES por culto o fecha y por tipo. NO se registra quién dio: esta
tabla no tiene ninguna columna que la ligue con una persona donante (D17 y #25). Un
ingreso nunca se borra: se anula con motivo.
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
from app.modelos.listas import TIPOS_INGRESO, TIPOS_SERVICIO
from app.modelos.utilidades import lista_sql


class Ingreso(Base):
    """Una cantidad de dinero recibida por una iglesia."""

    __tablename__ = "ingresos"

    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)

    iglesia_id: Mapped[int] = mapped_column(
        ForeignKey("iglesias.id", ondelete="RESTRICT", name="fk_ingresos_iglesia_id"),
        nullable=False,
    )

    # Fecha del ingreso (por ejemplo, el domingo del culto).
    fecha: Mapped[date] = mapped_column(Date, nullable=False)

    # Culto al que corresponde (opcional: no todo ingreso es de un culto).
    tipo_servicio: Mapped[str | None] = mapped_column(String(20))

    # Uno de los 5 tipos: diezmos, ofrendas, evami, talento u otras.
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)

    # Dinero: NUMERIC(12,2) y siempre mayor que 0 (CHECK más abajo).
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Obligatoria cuando el tipo es "otras" (por ejemplo, la petición de una hermana).
    descripcion: Mapped[str | None] = mapped_column(Text)

    # Quién CAPTURÓ el ingreso (un usuario), NO quien dio el dinero. Pendiente de confirmar
    # con Marcos (duda 1): si no se permite, se quita esta columna.
    registrado_por: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT", name="fk_ingresos_registrado_por"),
        nullable=False,
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # --- Anulación: los ingresos no se borran, se anulan con motivo (#25) ---
    # "Anulado" significa anulado_en IS NOT NULL; así no hay estados contradictorios.
    anulado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    anulado_motivo: Mapped[str | None] = mapped_column(Text)
    anulado_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT", name="fk_ingresos_anulado_por")
    )

    __table_args__ = (
        CheckConstraint(f"tipo IN ({lista_sql(TIPOS_INGRESO)})", name="ck_ingresos_tipo"),
        CheckConstraint(
            f"tipo_servicio IS NULL OR tipo_servicio IN ({lista_sql(TIPOS_SERVICIO)})",
            name="ck_ingresos_tipo_servicio",
        ),
        # El dinero siempre es mayor que cero.
        CheckConstraint("monto > 0", name="ck_ingresos_monto_positivo"),
        # Las "otras donaciones" exigen una descripción que no esté vacía (#25).
        CheckConstraint(
            "tipo <> 'otras' OR btrim(coalesce(descripcion, '')) <> ''",
            name="ck_ingresos_otras_descripcion",
        ),
        # Anular exige motivo (no vacío), fecha y quién; o no hay anulación (nada a medias).
        CheckConstraint(
            "(anulado_en IS NULL AND anulado_motivo IS NULL AND anulado_por IS NULL) "
            "OR (anulado_en IS NOT NULL AND btrim(coalesce(anulado_motivo, '')) <> '' "
            "AND anulado_por IS NOT NULL)",
            name="ck_ingresos_anulacion",
        ),
    )
