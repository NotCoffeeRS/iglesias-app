"""Pruebas de los modelos y de las migraciones del esquema inicial (Issue #4).

Primer PR: `iglesias` y `usuarios`. Segundo PR: las otras 13 tablas (sedes, redes
sociales, horarios, miembros, menores, tutores, grupos, asistencias, ingresos, gastos,
eventos y comunicados).

Estas pruebas necesitan PostgreSQL de verdad (no SQLite): los CHECK, los índices
únicos (también el parcial) y las llaves foráneas se comportan distinto. Si no hay una
DATABASE_URL de PostgreSQL, las pruebas FALLAN con un mensaje claro (no se saltan).

Cada prueba trabaja en una base temporal que se crea y se borra sola, así que no toca
tus datos.
"""

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, delete, inspect, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.db import Base
from app.modelos import (
    CARGOS,
    Asistencia,
    Comunicado,
    Evento,
    Gasto,
    Grupo,
    GrupoMiembro,
    Horario,
    Iglesia,
    Ingreso,
    Menor,
    Miembro,
    RedSocial,
    Sede,
    Tutor,
    Usuario,
)
from app.modelos.listas import (
    CATEGORIAS_GASTO,
    ESTADOS_MIEMBRO,
    TIPOS_GRUPO,
    TIPOS_INGRESO,
    TIPOS_SERVICIO,
)
from app.modelos.utilidades import obtener_url_base_datos

# Las 15 tablas del esquema inicial (2 del primer PR + 13 del segundo).
TABLAS_PRIMER_PR = {"iglesias", "usuarios"}
TABLAS_ESPERADAS = TABLAS_PRIMER_PR | {
    "sedes",
    "redes_sociales",
    "horarios",
    "miembros",
    "menores",
    "tutores",
    "grupos",
    "grupo_miembros",
    "asistencias",
    "ingresos",
    "gastos",
    "eventos",
    "comunicados",
}

# Ruta de backend/alembic.ini (este archivo está en backend/tests/).
RUTA_ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"

MENSAJE_SIN_POSTGRES = (
    "No hay una base PostgreSQL configurada para las pruebas. Define DATABASE_URL en el "
    "entorno o en backend/.env, por ejemplo: "
    "postgresql+psycopg://postgres:TU_CONTRASENA@localhost:5432/postgres . "
    "Estas pruebas no se saltan ni se ejecutan con SQLite a propósito: la versión de "
    "PostgreSQL de desarrollo debe ser la misma que la de Neon."
)

MENSAJE_SIN_CONEXION = (
    "No se pudo crear la base temporal de pruebas en PostgreSQL. Revisa que el servicio "
    "esté corriendo, que la contraseña de DATABASE_URL sea la correcta y que ese usuario "
    "pueda crear bases de datos (CREATEDB)."
)


@pytest.fixture(scope="module")
def url_servidor() -> URL:
    """URL del servidor PostgreSQL; si no hay una, la prueba falla con un mensaje claro."""
    texto = obtener_url_base_datos()
    if not texto or not texto.startswith("postgresql"):
        pytest.fail(MENSAJE_SIN_POSTGRES, pytrace=False)
    return make_url(texto)


@contextmanager
def _base_temporal(url_servidor: URL) -> Iterator[URL]:
    """Crea una base vacía con nombre único, la entrega y al final la borra."""
    # Nombre aleatorio y seguro (solo letras, números y guion bajo) para no chocar con nada.
    nombre = f"iglesias_prueba_{uuid.uuid4().hex[:12]}"
    # AUTOCOMMIT: CREATE/DROP DATABASE no pueden ir dentro de una transacción.
    motor_admin = create_engine(url_servidor, isolation_level="AUTOCOMMIT")
    try:
        conexion_fallo = False
        try:
            with motor_admin.connect() as conexion:
                conexion.execute(text(f'CREATE DATABASE "{nombre}"'))
        except DBAPIError:
            conexion_fallo = True
        if conexion_fallo:
            # Se avisa FUERA del except para que pytest no muestre el error original,
            # que podría incluir datos de conexión.
            pytest.fail(MENSAJE_SIN_CONEXION, pytrace=False)
        try:
            yield url_servidor.set(database=nombre)
        finally:
            with motor_admin.connect() as conexion:
                # WITH (FORCE) cierra conexiones que hayan quedado abiertas.
                conexion.execute(text(f'DROP DATABASE IF EXISTS "{nombre}" WITH (FORCE)'))
    finally:
        motor_admin.dispose()


def _config_alembic(url: URL) -> Config:
    """Configuración de Alembic que apunta a la base temporal (la URL no se escribe en texto)."""
    config = Config(str(RUTA_ALEMBIC_INI))
    config.attributes["url"] = url
    return config


@pytest.fixture
def base_temporal(url_servidor: URL) -> Iterator[URL]:
    """Una base temporal vacía para cada prueba que la pida."""
    with _base_temporal(url_servidor) as url:
        yield url


@pytest.fixture(scope="module")
def motor_migrado(url_servidor: URL) -> Iterator:
    """Una base temporal con la migración ya aplicada, compartida por todo este archivo."""
    with _base_temporal(url_servidor) as url:
        command.upgrade(_config_alembic(url), "head")
        motor = create_engine(url)
        yield motor
        motor.dispose()


@pytest.fixture
def sesion(motor_migrado) -> Iterator[Session]:
    """Una sesión cuyos cambios se deshacen al terminar la prueba (no deja datos)."""
    conexion = motor_migrado.connect()
    transaccion = conexion.begin()
    sesion = Session(bind=conexion)
    try:
        yield sesion
    finally:
        sesion.close()
        # Deshace todo lo que hizo la prueba. Si un error de la base ya cerró la
        # transacción (pasa en las pruebas que esperan un IntegrityError), no hay nada que deshacer.
        if transaccion.is_active:
            transaccion.rollback()
        conexion.close()


def _crear_iglesia(sesion: Session) -> Iglesia:
    """Inserta una iglesia ficticia con nombre único y devuelve el objeto con su id."""
    iglesia = Iglesia(nombre=f"Iglesia de prueba {uuid.uuid4().hex[:8]}")
    sesion.add(iglesia)
    sesion.flush()  # envía el INSERT a la base para que se validen las restricciones
    return iglesia


def _nuevo_usuario(nombre_usuario: str, cargo: str, iglesia_id: int | None) -> Usuario:
    """Arma un usuario ficticio. El "hash" es un texto inventado, no una contraseña real."""
    return Usuario(
        nombre_usuario=nombre_usuario,
        contrasena_hash="hash-inventado-solo-para-pruebas",
        nombre_completo="Persona de Prueba",
        cargo=cargo,
        iglesia_id=iglesia_id,
    )


def test_upgrade_y_downgrade(base_temporal: URL) -> None:
    """`upgrade head` crea las tablas, `downgrade base` las quita y se puede volver a subir."""
    config = _config_alembic(base_temporal)
    motor = create_engine(base_temporal)
    try:
        command.upgrade(config, "head")
        # Además de las 15 tablas existe `alembic_version`, la cuenta interna de Alembic.
        assert set(inspect(motor).get_table_names()) == TABLAS_ESPERADAS | {"alembic_version"}

        command.downgrade(config, "base")
        # Solo queda la tabla interna de Alembic que lleva la cuenta de las migraciones.
        assert set(inspect(motor).get_table_names()) == {"alembic_version"}

        command.upgrade(config, "head")
        assert set(inspect(motor).get_table_names()) == TABLAS_ESPERADAS | {"alembic_version"}
    finally:
        motor.dispose()


def test_las_migraciones_estan_encadenadas() -> None:
    """La 0002 depende de la 0001 y hay una sola cabeza (no se bifurca la historia)."""
    script = ScriptDirectory.from_config(Config(str(RUTA_ALEMBIC_INI)))
    assert script.get_heads() == ["0002"]
    assert script.get_revision("0002").down_revision == "0001"
    assert script.get_revision("0001").down_revision is None


def test_bajar_solo_la_0002_deja_intacto_el_primer_pr(base_temporal: URL) -> None:
    """`downgrade 0001` quita las 13 tablas nuevas y conserva iglesias y usuarios."""
    config = _config_alembic(base_temporal)
    motor = create_engine(base_temporal)
    try:
        command.upgrade(config, "head")
        command.downgrade(config, "0001")
        assert set(inspect(motor).get_table_names()) == TABLAS_PRIMER_PR | {"alembic_version"}
        command.upgrade(config, "head")  # y se puede volver a subir
        assert set(inspect(motor).get_table_names()) == TABLAS_ESPERADAS | {"alembic_version"}
    finally:
        motor.dispose()


def test_modelos_coinciden_con_la_migracion(motor_migrado) -> None:
    """Los modelos de Python y la migración describen exactamente las mismas tablas."""
    with motor_migrado.connect() as conexion:
        contexto = MigrationContext.configure(conexion, opts={"compare_type": True})
        diferencias = compare_metadata(contexto, Base.metadata)
    assert diferencias == []


def test_solo_se_guarda_el_hash_de_la_contrasena() -> None:
    """Existe `contrasena_hash` y no hay ninguna columna para la contraseña en texto."""
    columnas = Usuario.__table__.columns.keys()
    assert "contrasena_hash" in columnas
    assert "contrasena" not in columnas


def test_valores_por_defecto_de_un_usuario(sesion: Session) -> None:
    """Un usuario nuevo queda activo y con fecha de creación con zona horaria."""
    iglesia = _crear_iglesia(sesion)
    usuario = _nuevo_usuario("usuario.defecto", "pastor", iglesia.id)
    sesion.add(usuario)
    sesion.flush()
    sesion.refresh(usuario)  # vuelve a leer los valores que puso PostgreSQL
    assert usuario.activo is True
    assert usuario.creado_en.tzinfo is not None


@pytest.mark.parametrize("cargo", CARGOS)
def test_cada_cargo_de_la_lista_se_acepta(sesion: Session, cargo: str) -> None:
    """Los 13 cargos de la lista cerrada se pueden guardar (con la iglesia que les toca)."""
    # El presbítero va sin iglesia; los demás cargos llevan una.
    iglesia_id = None if cargo == "presbitero" else _crear_iglesia(sesion).id
    usuario = _nuevo_usuario(f"usuario.{cargo}", cargo, iglesia_id)
    sesion.add(usuario)
    sesion.flush()
    assert usuario.id is not None


def test_cargo_invalido_se_rechaza(sesion: Session) -> None:
    """Un cargo que no está en la lista cerrada falla por el CHECK ck_usuarios_cargo."""
    iglesia = _crear_iglesia(sesion)
    sesion.add(_nuevo_usuario("usuario.cargo.invalido", "jardinero", iglesia.id))
    with pytest.raises(IntegrityError, match="ck_usuarios_cargo"):
        sesion.flush()


@pytest.mark.parametrize("cargo", [cargo for cargo in CARGOS if cargo != "presbitero"])
def test_cargo_distinto_de_presbitero_sin_iglesia_se_rechaza(sesion: Session, cargo: str) -> None:
    """Solo el presbítero puede no tener iglesia; cualquier otro cargo sin iglesia falla."""
    sesion.add(_nuevo_usuario(f"sin.iglesia.{cargo}", cargo, None))
    with pytest.raises(IntegrityError, match="ck_usuarios_iglesia_segun_cargo"):
        sesion.flush()


def test_nombre_de_usuario_duplicado_en_otras_mayusculas_se_rechaza(sesion: Session) -> None:
    """"Maria.Lopez" y "maria.lopez" cuentan como el mismo usuario."""
    iglesia = _crear_iglesia(sesion)
    sesion.add(_nuevo_usuario("Maria.Lopez", "tesorero", iglesia.id))
    sesion.flush()  # el primero se guarda bien
    sesion.add(_nuevo_usuario("maria.lopez", "ujier", iglesia.id))
    with pytest.raises(IntegrityError, match="uq_usuarios_nombre_usuario_minusculas"):
        sesion.flush()


def test_nombre_de_iglesia_duplicado_se_rechaza(sesion: Session) -> None:
    """No puede haber dos iglesias con el mismo nombre."""
    sesion.add(Iglesia(nombre="Iglesia repetida de prueba"))
    sesion.flush()
    sesion.add(Iglesia(nombre="Iglesia repetida de prueba"))
    with pytest.raises(IntegrityError, match="uq_iglesias_nombre"):
        sesion.flush()


def test_borrar_una_iglesia_con_usuarios_falla(sesion: Session) -> None:
    """No se puede borrar una iglesia que todavía tiene usuarios (llave foránea RESTRICT)."""
    iglesia = _crear_iglesia(sesion)
    sesion.add(_nuevo_usuario("usuario.de.la.iglesia", "pastor", iglesia.id))
    sesion.flush()
    with pytest.raises(IntegrityError, match="fk_usuarios_iglesia_id"):
        sesion.execute(delete(Iglesia).where(Iglesia.id == iglesia.id))


# =============================================================================
# Segundo PR del Issue #4: las otras 13 tablas
# =============================================================================


def _guardar(sesion: Session, objeto):
    """Agrega un objeto, lo envía a la base (para validar las restricciones) y lo devuelve."""
    sesion.add(objeto)
    sesion.flush()
    return objeto


def _base(sesion: Session) -> tuple[Iglesia, Usuario]:
    """Una iglesia y un usuario ficticios, que casi todas las demás tablas necesitan."""
    iglesia = _crear_iglesia(sesion)
    usuario = _nuevo_usuario(f"usuario.{uuid.uuid4().hex[:10]}", "tesorero", iglesia.id)
    return iglesia, _guardar(sesion, usuario)


def _miembro(sesion: Session, iglesia: Iglesia, estado: str = "activo") -> Miembro:
    """Un miembro ficticio de la iglesia dada."""
    nombre = f"Miembro {uuid.uuid4().hex[:6]}"
    return _guardar(sesion, Miembro(nombre=nombre, iglesia_id=iglesia.id, estado=estado))


def _sede(sesion: Session, iglesia: Iglesia, nombre: str | None = None) -> Sede:
    """Una sede de la iglesia dada."""
    sede = Sede(
        iglesia_id=iglesia.id,
        nombre=nombre or f"Sede {uuid.uuid4().hex[:6]}",
        direccion="Calle inventada 123",
    )
    return _guardar(sesion, sede)


def _grupo(sesion: Session, iglesia: Iglesia, lider: Usuario, tipo: str = "celula") -> Grupo:
    """Un grupo del tipo dado, liderado por `lider`."""
    grupo = Grupo(
        iglesia_id=iglesia.id,
        tipo=tipo,
        nombre=f"Grupo {uuid.uuid4().hex[:6]}",
        lider_usuario_id=lider.id,
    )
    return _guardar(sesion, grupo)


def _nuevo_ingreso(iglesia: Iglesia, usuario: Usuario, **campos) -> Ingreso:
    """Arma un ingreso válido; `campos` cambia lo que cada prueba necesite."""
    datos = {
        "iglesia_id": iglesia.id,
        "fecha": date(2026, 11, 1),
        "tipo": "ofrendas",
        "monto": Decimal("100.00"),
        "registrado_por": usuario.id,
    }
    datos.update(campos)
    return Ingreso(**datos)


def _nuevo_gasto(iglesia: Iglesia, usuario: Usuario, **campos) -> Gasto:
    """Arma un gasto válido; `campos` cambia lo que cada prueba necesite."""
    datos = {
        "iglesia_id": iglesia.id,
        "fecha": date(2026, 11, 1),
        "categoria": "luz",
        "monto": Decimal("250.50"),
        "registrado_por": usuario.id,
    }
    datos.update(campos)
    return Gasto(**datos)


def _anulacion(usuario: Usuario, **cambios) -> dict:
    """Los tres campos de una anulación completa y válida (se puede cambiar alguno)."""
    datos = {
        "anulado_en": datetime.now(UTC),
        "anulado_motivo": "Monto capturado por error",
        "anulado_por": usuario.id,
    }
    datos.update(cambios)
    return datos


def _menor(sesion: Session, iglesia: Iglesia) -> Menor:
    """Un menor ficticio (niña de 2018) de la iglesia dada."""
    menor = Menor(
        iglesia_id=iglesia.id,
        nombre="Menor Inventada",
        fecha_nacimiento=date(2018, 5, 1),
        sexo="femenino",
    )
    return _guardar(sesion, menor)


def _marca(miembro: Miembro, usuario: Usuario, servicio: str, **campos) -> Asistencia:
    """Una marca de asistencia del miembro en un servicio del 1 de noviembre de 2026."""
    datos = {
        "miembro_id": miembro.id,
        "fecha": date(2026, 11, 1),
        "tipo_servicio": servicio,
        "presente": True,
        "registrado_por": usuario.id,
    }
    datos.update(campos)
    return Asistencia(**datos)


# --- Listas cerradas ---------------------------------------------------------


def test_las_listas_cerradas_tienen_los_valores_del_issue() -> None:
    """6 estados de miembro, 8 tipos de servicio, 5 de ingreso y 8 categorías de gasto (#4)."""
    assert len(ESTADOS_MIEMBRO) == 6
    assert len(TIPOS_SERVICIO) == 8
    assert len(TIPOS_INGRESO) == 5
    assert len(CATEGORIAS_GASTO) == 8
    assert len(TIPOS_GRUPO) == 5


@pytest.mark.parametrize("estado", ESTADOS_MIEMBRO)
def test_cada_estado_de_miembro_se_acepta(sesion: Session, estado: str) -> None:
    """Los 6 estados de miembro se pueden guardar."""
    iglesia = _crear_iglesia(sesion)
    assert _miembro(sesion, iglesia, estado).id is not None


def test_estado_de_miembro_invalido_se_rechaza(sesion: Session) -> None:
    """Un estado que no está en la lista cerrada falla por el CHECK."""
    iglesia = _crear_iglesia(sesion)
    sesion.add(Miembro(nombre="Miembro Inventado", iglesia_id=iglesia.id, estado="jubilado"))
    with pytest.raises(IntegrityError, match="ck_miembros_estado"):
        sesion.flush()


def test_estado_civil_invalido_se_rechaza(sesion: Session) -> None:
    """El estado civil, si se da, debe ser de la lista cerrada."""
    iglesia = _crear_iglesia(sesion)
    sesion.add(
        Miembro(
            nombre="Miembro Inventado",
            iglesia_id=iglesia.id,
            estado="activo",
            estado_civil="complicado",
        )
    )
    with pytest.raises(IntegrityError, match="ck_miembros_estado_civil"):
        sesion.flush()


def test_un_miembro_puede_no_tener_fecha_de_ingreso(sesion: Session) -> None:
    """Un visitante todavía no tiene fecha de ingreso a la congregación (es opcional)."""
    iglesia = _crear_iglesia(sesion)
    visitante = _miembro(sesion, iglesia, "visitante")
    assert visitante.fecha_ingreso is None


@pytest.mark.parametrize("tipo", TIPOS_SERVICIO)
def test_cada_tipo_de_servicio_se_acepta_en_horarios(sesion: Session, tipo: str) -> None:
    """Los 8 tipos de servicio se pueden usar en un horario."""
    sede = _sede(sesion, _crear_iglesia(sesion))
    horario = Horario(sede_id=sede.id, tipo=tipo, dia="domingo", hora_inicio=time(10, 0))
    assert _guardar(sesion, horario).id is not None


def test_tipo_de_servicio_invalido_se_rechaza(sesion: Session) -> None:
    """Un tipo de servicio fuera de la lista falla por el CHECK."""
    sede = _sede(sesion, _crear_iglesia(sesion))
    sesion.add(Horario(sede_id=sede.id, tipo="concierto", dia="domingo", hora_inicio=time(10, 0)))
    with pytest.raises(IntegrityError, match="ck_horarios_tipo"):
        sesion.flush()


@pytest.mark.parametrize("tipo", TIPOS_GRUPO)
def test_cada_tipo_de_grupo_se_acepta(sesion: Session, tipo: str) -> None:
    """Los 5 tipos de grupo se pueden guardar."""
    iglesia, lider = _base(sesion)
    assert _grupo(sesion, iglesia, lider, tipo).id is not None


def test_tipo_de_grupo_invalido_se_rechaza(sesion: Session) -> None:
    """Un tipo de grupo fuera de la lista falla por el CHECK."""
    iglesia, lider = _base(sesion)
    sesion.add(Grupo(iglesia_id=iglesia.id, tipo="club", nombre="Club", lider_usuario_id=lider.id))
    with pytest.raises(IntegrityError, match="ck_grupos_tipo"):
        sesion.flush()


@pytest.mark.parametrize("tipo", TIPOS_INGRESO)
def test_cada_tipo_de_ingreso_se_acepta(sesion: Session, tipo: str) -> None:
    """Los 5 tipos de ingreso se pueden guardar (con descripción, que "otras" exige)."""
    iglesia, usuario = _base(sesion)
    ingreso = _nuevo_ingreso(iglesia, usuario, tipo=tipo, descripcion="Detalle del ingreso")
    assert _guardar(sesion, ingreso).id is not None


def test_tipo_de_ingreso_invalido_se_rechaza(sesion: Session) -> None:
    """Un tipo de ingreso fuera de la lista falla por el CHECK."""
    iglesia, usuario = _base(sesion)
    sesion.add(_nuevo_ingreso(iglesia, usuario, tipo="rifa"))
    with pytest.raises(IntegrityError, match="ck_ingresos_tipo"):
        sesion.flush()


@pytest.mark.parametrize("categoria", CATEGORIAS_GASTO)
def test_cada_categoria_de_gasto_se_acepta(sesion: Session, categoria: str) -> None:
    """Las 8 categorías de gasto se pueden guardar."""
    iglesia, usuario = _base(sesion)
    assert _guardar(sesion, _nuevo_gasto(iglesia, usuario, categoria=categoria)).id is not None


def test_categoria_de_gasto_invalida_se_rechaza(sesion: Session) -> None:
    """Una categoría fuera de la lista falla por el CHECK."""
    iglesia, usuario = _base(sesion)
    sesion.add(_nuevo_gasto(iglesia, usuario, categoria="vacaciones"))
    with pytest.raises(IntegrityError, match="ck_gastos_categoria"):
        sesion.flush()


# --- Dinero: ingresos y gastos -----------------------------------------------


@pytest.mark.parametrize("tabla", ["ingresos", "gastos"])
def test_el_dinero_es_numeric_12_2(motor_migrado, tabla: str) -> None:
    """La columna `monto` es NUMERIC(12,2) en ingresos y en gastos (#4)."""
    columnas = {c["name"]: c for c in inspect(motor_migrado).get_columns(tabla)}
    tipo = columnas["monto"]["type"]
    assert (tipo.precision, tipo.scale) == (12, 2)


@pytest.mark.parametrize("monto", [Decimal("0"), Decimal("-1.00")])
def test_ingreso_con_monto_cero_o_negativo_se_rechaza(sesion: Session, monto: Decimal) -> None:
    """El monto de un ingreso debe ser mayor que 0."""
    iglesia, usuario = _base(sesion)
    sesion.add(_nuevo_ingreso(iglesia, usuario, monto=monto))
    with pytest.raises(IntegrityError, match="ck_ingresos_monto_positivo"):
        sesion.flush()


@pytest.mark.parametrize("monto", [Decimal("0"), Decimal("-1.00")])
def test_gasto_con_monto_cero_o_negativo_se_rechaza(sesion: Session, monto: Decimal) -> None:
    """El monto de un gasto debe ser mayor que 0."""
    iglesia, usuario = _base(sesion)
    sesion.add(_nuevo_gasto(iglesia, usuario, monto=monto))
    with pytest.raises(IntegrityError, match="ck_gastos_monto_positivo"):
        sesion.flush()


@pytest.mark.parametrize("descripcion", [None, "", "   "])
def test_ingreso_otras_sin_descripcion_se_rechaza(sesion: Session, descripcion) -> None:
    """Las "otras donaciones" exigen una descripción que no esté vacía (#25)."""
    iglesia, usuario = _base(sesion)
    sesion.add(_nuevo_ingreso(iglesia, usuario, tipo="otras", descripcion=descripcion))
    with pytest.raises(IntegrityError, match="ck_ingresos_otras_descripcion"):
        sesion.flush()


def test_ingresos_no_tienen_ninguna_columna_de_persona(motor_migrado) -> None:
    """Ningún ingreso se liga a una persona donante (D17 y #25)."""
    inspector = inspect(motor_migrado)
    columnas = [c["name"] for c in inspector.get_columns("ingresos")]
    # Ninguna columna de persona: ni "miembro", ni "donante", ni "persona", ni "tutor".
    for palabra in ("miembro", "donante", "persona", "tutor", "menor"):
        assert not [c for c in columnas if palabra in c], f"hay una columna con '{palabra}'"
    # Y ninguna llave foránea hacia miembros, menores o tutores: solo iglesias y usuarios
    # (usuarios = quien CAPTURÓ el ingreso, no quien dio; duda 1 pendiente de Marcos).
    destinos = {fk["referred_table"] for fk in inspector.get_foreign_keys("ingresos")}
    assert destinos <= {"iglesias", "usuarios"}


@pytest.mark.parametrize("fabrica", [_nuevo_ingreso, _nuevo_gasto], ids=["ingresos", "gastos"])
def test_una_anulacion_completa_se_acepta(sesion: Session, fabrica) -> None:
    """Anular = fecha + motivo + quién. Así se "borra" un ingreso o gasto: sin borrarlo."""
    iglesia, usuario = _base(sesion)
    registro = _guardar(sesion, fabrica(iglesia, usuario, **_anulacion(usuario)))
    assert registro.anulado_en is not None


@pytest.mark.parametrize("fabrica", [_nuevo_ingreso, _nuevo_gasto], ids=["ingresos", "gastos"])
@pytest.mark.parametrize(
    "cambios",
    [
        {"anulado_motivo": None},  # anulado, pero sin motivo
        {"anulado_motivo": "   "},  # motivo en blanco
        {"anulado_por": None},  # anulado, pero sin decir quién
        {"anulado_en": None},  # motivo y quién, pero sin fecha de anulación
    ],
    ids=["sin_motivo", "motivo_en_blanco", "sin_quien", "sin_fecha"],
)
def test_una_anulacion_a_medias_se_rechaza(sesion: Session, fabrica, cambios: dict) -> None:
    """La anulación va completa o no va: nunca a medias (#25 y #27)."""
    iglesia, usuario = _base(sesion)
    sesion.add(fabrica(iglesia, usuario, **_anulacion(usuario, **cambios)))
    with pytest.raises(IntegrityError, match="ck_.*_anulacion"):
        sesion.flush()


# --- Iglesias, sedes, redes y horarios ---------------------------------------


def test_una_iglesia_puede_tener_dos_sedes(sesion: Session) -> None:
    """La 3ra de Mérida tiene dos sedes: Madero y Kanasín (#12)."""
    iglesia = _crear_iglesia(sesion)
    assert _sede(sesion, iglesia, "Madero").id != _sede(sesion, iglesia, "Kanasín").id


def test_el_nombre_de_una_sede_no_se_repite_en_la_misma_iglesia(sesion: Session) -> None:
    """Dos sedes de la misma iglesia no pueden llamarse igual (pero en otra iglesia sí)."""
    iglesia, otra = _crear_iglesia(sesion), _crear_iglesia(sesion)
    _sede(sesion, iglesia, "Centro")
    _sede(sesion, otra, "Centro")  # mismo nombre en OTRA iglesia: permitido
    sesion.add(Sede(iglesia_id=iglesia.id, nombre="Centro", direccion="Otra calle"))
    with pytest.raises(IntegrityError, match="uq_sedes_iglesia_nombre"):
        sesion.flush()


@pytest.mark.parametrize("tipo", ["propia", "relacionada"])
def test_cada_tipo_de_red_social_se_acepta(sesion: Session, tipo: str) -> None:
    """Las redes sociales pueden ser propias o relacionadas (#12)."""
    iglesia = _crear_iglesia(sesion)
    red = RedSocial(iglesia_id=iglesia.id, nombre="Facebook", url="https://ejemplo.mx", tipo=tipo)
    assert _guardar(sesion, red).id is not None


def test_tipo_de_red_social_invalido_se_rechaza(sesion: Session) -> None:
    """Un tipo de red social fuera de la lista falla por el CHECK."""
    iglesia = _crear_iglesia(sesion)
    sesion.add(RedSocial(iglesia_id=iglesia.id, nombre="X", url="https://ejemplo.mx", tipo="otra"))
    with pytest.raises(IntegrityError, match="ck_redes_sociales_tipo"):
        sesion.flush()


def test_una_sede_puede_tener_varios_horarios_del_mismo_tipo(sesion: Session) -> None:
    """Dos horarios del mismo tipo en la misma sede, en días distintos, son válidos (#14)."""
    sede = _sede(sesion, _crear_iglesia(sesion))
    martes = Horario(sede_id=sede.id, tipo="oracion", dia="martes", hora_inicio=time(6, 0))
    jueves = Horario(sede_id=sede.id, tipo="oracion", dia="jueves", hora_inicio=time(6, 0))
    assert _guardar(sesion, martes).id != _guardar(sesion, jueves).id


def test_un_horario_exactamente_igual_se_rechaza(sesion: Session) -> None:
    """No se puede repetir el mismo horario (misma sede, tipo, día y hora)."""
    sede = _sede(sesion, _crear_iglesia(sesion))
    _guardar(sesion, Horario(sede_id=sede.id, tipo="jovenes", dia="sabado", hora_inicio=time(19)))
    sesion.add(Horario(sede_id=sede.id, tipo="jovenes", dia="sabado", hora_inicio=time(19)))
    with pytest.raises(IntegrityError, match="uq_horarios_sede_tipo_dia_hora"):
        sesion.flush()


def test_dia_invalido_en_un_horario_se_rechaza(sesion: Session) -> None:
    """El día debe ser uno de los 7 de la semana."""
    sede = _sede(sesion, _crear_iglesia(sesion))
    sesion.add(Horario(sede_id=sede.id, tipo="dna", dia="festivo", hora_inicio=time(10, 0)))
    with pytest.raises(IntegrityError, match="ck_horarios_dia"):
        sesion.flush()


@pytest.mark.parametrize("hora_fin", [time(10, 0), time(9, 0)])
def test_hora_de_fin_no_posterior_a_la_de_inicio_se_rechaza(
    sesion: Session, hora_fin: time
) -> None:
    """Si hay hora de fin, debe ser posterior a la de inicio."""
    sede = _sede(sesion, _crear_iglesia(sesion))
    sesion.add(
        Horario(
            sede_id=sede.id, tipo="dna", dia="lunes", hora_inicio=time(10, 0), hora_fin=hora_fin
        )
    )
    with pytest.raises(IntegrityError, match="ck_horarios_hora_fin"):
        sesion.flush()


# --- Menores y tutores -------------------------------------------------------


def test_sexo_invalido_de_un_menor_se_rechaza(sesion: Session) -> None:
    """El sexo del menor es de una lista cerrada (la categoría depende de él, #19)."""
    iglesia = _crear_iglesia(sesion)
    sesion.add(
        Menor(
            iglesia_id=iglesia.id,
            nombre="Menor Inventado",
            fecha_nacimiento=date(2018, 5, 1),
            sexo="x",
        )
    )
    with pytest.raises(IntegrityError, match="ck_menores_sexo"):
        sesion.flush()


def test_la_categoria_del_menor_no_se_guarda() -> None:
    """La categoría (niño, niña o adolescente) se calcula, no se captura a mano (#19)."""
    assert "categoria" not in Menor.__table__.columns.keys()


def test_un_tutor_necesita_nombre_y_telefono(sesion: Session) -> None:
    """Los tutores llevan nombre y teléfono obligatorios (#19)."""
    menor = _menor(sesion, _crear_iglesia(sesion))
    tutor = _guardar(sesion, Tutor(menor_id=menor.id, nombre="Tutor Uno", telefono="9990000000"))
    assert tutor.id is not None
    sesion.add(Tutor(menor_id=menor.id, nombre="Tutor Dos", telefono=None))
    with pytest.raises(IntegrityError, match="telefono"):
        sesion.flush()


# --- Grupos y miembros de grupos ---------------------------------------------


def test_el_lider_y_el_asistente_no_pueden_ser_la_misma_persona(sesion: Session) -> None:
    """El líder y el asistente de un grupo deben ser personas distintas."""
    iglesia, lider = _base(sesion)
    sesion.add(
        Grupo(
            iglesia_id=iglesia.id,
            tipo="celula",
            nombre="Célula uno",
            lider_usuario_id=lider.id,
            asistente_usuario_id=lider.id,
        )
    )
    with pytest.raises(IntegrityError, match="ck_grupos_lider_distinto_asistente"):
        sesion.flush()


def test_un_grupo_necesita_lider(sesion: Session) -> None:
    """El líder es obligatorio (#4: grupos "con líder y asistente")."""
    iglesia = _crear_iglesia(sesion)
    sesion.add(Grupo(iglesia_id=iglesia.id, tipo="celula", nombre="Sin líder"))
    with pytest.raises(IntegrityError, match="lider_usuario_id"):
        sesion.flush()


def test_el_asistente_de_un_grupo_es_opcional(sesion: Session) -> None:
    """Un grupo puede no tener asistente."""
    iglesia, lider = _base(sesion)
    assert _grupo(sesion, iglesia, lider).asistente_usuario_id is None


def test_el_nombre_de_un_grupo_no_se_repite_en_su_iglesia_y_tipo(sesion: Session) -> None:
    """Dos grupos del mismo tipo y la misma iglesia no pueden llamarse igual."""
    iglesia, lider = _base(sesion)
    datos = {
        "iglesia_id": iglesia.id,
        "tipo": "celula",
        "nombre": "Célula Norte",
        "lider_usuario_id": lider.id,
    }
    _guardar(sesion, Grupo(**datos))
    sesion.add(Grupo(**datos))
    with pytest.raises(IntegrityError, match="uq_grupos_iglesia_tipo_nombre"):
        sesion.flush()


def test_un_miembro_solo_puede_estar_en_una_celula(sesion: Session) -> None:
    """La segunda célula de un miembro se rechaza (suposición del #22, pendiente)."""
    iglesia, lider = _base(sesion)
    miembro = _miembro(sesion, iglesia)
    primera, segunda = _grupo(sesion, iglesia, lider), _grupo(sesion, iglesia, lider)
    _guardar(sesion, GrupoMiembro(grupo_id=primera.id, miembro_id=miembro.id, tipo_grupo="celula"))
    sesion.add(GrupoMiembro(grupo_id=segunda.id, miembro_id=miembro.id, tipo_grupo="celula"))
    with pytest.raises(IntegrityError, match="uq_grupo_miembros_una_celula"):
        sesion.flush()


def test_un_miembro_puede_estar_en_varios_ministerios(sesion: Session) -> None:
    """La regla de "una sola" es solo para células: los ministerios pueden ser varios (#22)."""
    iglesia, lider = _base(sesion)
    miembro = _miembro(sesion, iglesia)
    for _ in range(2):
        ministerio = _grupo(sesion, iglesia, lider, "ministerio")
        union = GrupoMiembro(grupo_id=ministerio.id, miembro_id=miembro.id, tipo_grupo="ministerio")
        _guardar(sesion, union)


def test_el_tipo_copiado_en_grupo_miembros_debe_coincidir_con_el_del_grupo(
    sesion: Session,
) -> None:
    """No se puede decir que un ministerio es una célula (la llave compuesta lo impide)."""
    iglesia, lider = _base(sesion)
    miembro = _miembro(sesion, iglesia)
    ministerio = _grupo(sesion, iglesia, lider, "ministerio")
    sesion.add(GrupoMiembro(grupo_id=ministerio.id, miembro_id=miembro.id, tipo_grupo="celula"))
    with pytest.raises(IntegrityError, match="fk_grupo_miembros_grupo_tipo"):
        sesion.flush()


# --- Asistencias -------------------------------------------------------------


def test_una_persona_no_se_marca_dos_veces_el_mismo_dia_y_servicio(sesion: Session) -> None:
    """La misma persona, fecha y servicio no se repite (#23); en otro servicio sí se puede."""
    iglesia, usuario = _base(sesion)
    miembro = _miembro(sesion, iglesia)
    _guardar(sesion, _marca(miembro, usuario, "culto_domingo"))
    _guardar(sesion, _marca(miembro, usuario, "oracion"))  # otro servicio, mismo día: permitido
    sesion.add(_marca(miembro, usuario, "culto_domingo"))
    with pytest.raises(IntegrityError, match="uq_asistencias_miembro_fecha_servicio"):
        sesion.flush()


def test_tipo_de_servicio_invalido_en_asistencias_se_rechaza(sesion: Session) -> None:
    """El servicio de una asistencia es de la lista cerrada de 8."""
    iglesia, usuario = _base(sesion)
    miembro = _miembro(sesion, iglesia)
    sesion.add(_marca(miembro, usuario, "fiesta", presente=False))
    with pytest.raises(IntegrityError, match="ck_asistencias_tipo_servicio"):
        sesion.flush()


# --- Eventos y comunicados ---------------------------------------------------


@pytest.mark.parametrize("de_una_iglesia", [True, False], ids=["una_iglesia", "presbiterio"])
def test_un_evento_puede_ser_de_una_iglesia_o_de_todo_el_presbiterio(
    sesion: Session, de_una_iglesia: bool
) -> None:
    """`iglesia_id` vacío significa "todo el Presbiterio" (#32)."""
    iglesia, usuario = _base(sesion)
    evento = Evento(
        titulo="Evento inventado",
        fecha=date(2026, 11, 8),
        hora=time(19, 0),
        iglesia_id=iglesia.id if de_una_iglesia else None,
        creado_por=usuario.id,
    )
    assert _guardar(sesion, evento).id is not None


@pytest.mark.parametrize("de_una_iglesia", [True, False], ids=["una_iglesia", "presbiterio"])
def test_un_comunicado_puede_ser_de_una_iglesia_o_de_todo_el_presbiterio(
    sesion: Session, de_una_iglesia: bool
) -> None:
    """`iglesia_id` vacío significa "todo el Presbiterio" (#33)."""
    iglesia, usuario = _base(sesion)
    comunicado = Comunicado(
        titulo="Aviso inventado",
        contenido="Texto de prueba",
        iglesia_id=iglesia.id if de_una_iglesia else None,
        vigente_hasta=date(2099, 12, 31),
        creado_por=usuario.id,
    )
    assert _guardar(sesion, comunicado).id is not None


def test_la_vigencia_no_puede_terminar_antes_de_la_publicacion(sesion: Session) -> None:
    """Un comunicado cuya vigencia ya venció desde su publicación se rechaza."""
    iglesia, usuario = _base(sesion)
    sesion.add(
        Comunicado(
            titulo="Aviso viejo",
            contenido="Texto de prueba",
            iglesia_id=iglesia.id,
            vigente_hasta=date(2020, 1, 1),
            creado_por=usuario.id,
        )
    )
    with pytest.raises(IntegrityError, match="ck_comunicados_vigencia"):
        sesion.flush()


# --- Nada se borra en cascada ------------------------------------------------


def test_no_se_borra_una_iglesia_con_sedes(sesion: Session) -> None:
    """Las llaves foráneas son RESTRICT: no se borra una iglesia que tiene sedes."""
    iglesia = _crear_iglesia(sesion)
    _sede(sesion, iglesia)
    with pytest.raises(IntegrityError, match="fk_sedes_iglesia_id"):
        sesion.execute(delete(Iglesia).where(Iglesia.id == iglesia.id))


def test_no_se_borra_un_miembro_con_asistencias(sesion: Session) -> None:
    """No se borra un miembro que ya tiene asistencias registradas (se desactiva)."""
    iglesia, usuario = _base(sesion)
    miembro = _miembro(sesion, iglesia)
    _guardar(sesion, _marca(miembro, usuario, "culto_domingo"))
    with pytest.raises(IntegrityError, match="fk_asistencias_miembro_id"):
        sesion.execute(delete(Miembro).where(Miembro.id == miembro.id))
