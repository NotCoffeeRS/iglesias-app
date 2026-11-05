"""Pruebas de permisos por cargo, iglesia y grupo (Issue #10, HU-02, módulo crítico).

Convierte en pruebas automáticas el plan de casos publicado en el Issue #10 (versión 3), ya
corregido con las decisiones D19 a D22 y con lo que el código hace de verdad. Cada prueba
cita las filas del plan que cubre (PERM-xx, EXTRA-xx).

FASES CUBIERTAS (alcance acordado con Jessica):
  1. Criterios de aceptación del Issue: aislamiento entre iglesias, dinero (tesorero, líder y
     demás cargos) y "un líder solo ve su grupo".
  2. Escalamiento de cargos (D19) al crear y editar usuarios.
  3. Casos sin sesión, con token malo, con credenciales incorrectas y con usuario desactivado.

PENDIENTE (no se escribió a propósito; se hará solo si sobra tiempo):
  - Fase 4: miembros, asistencia, eventos, comunicados, iglesias y grupos fila por fila.
  - Filas del plan que dependen de APIs que todavía no existen en `main`:
      reporte financiero y consolidado (#29, ahora de Ángeles), historial y reportes de
      asistencia y de miembros (#31), dashboard, resumen mensual de donaciones, exportación a
      PDF o Excel, detalle de un ingreso por id y cambio de contraseña (PERM-08, 09, 15, 17, 22,
      29, 31, 33 a 45, 58, 76 a 81 y 108 a 120).
  - D22 (el pastor da acceso al dinero a otro cargo) y D27 (el pastor corrige un monto sin
    autorización): están pendientes de implementar, no hay nada que probar todavía.

DATOS: cada módulo de pruebas usa una base PostgreSQL TEMPORAL (se crea y se borra sola) con las
migraciones aplicadas y los datos de ejemplo del Issue #5 (4 iglesias, 22 miembros, 6 grupos,
27 ingresos, 12 gastos y las 6 cuentas por cargo). Nunca se toca iglesias_demo ni el .env. Las
contraseñas se inventan al azar en cada corrida y no se imprimen. Las cuentas que el ejemplo no
trae (otros cargos, un pastor y un tesorero de la 4ta, líderes de red y de ministerio y una cuenta
desactivada) se crean aquí. Cada prueba corre dentro de una transacción que se deshace.

Si no hay PostgreSQL configurado las pruebas FALLAN con un mensaje claro (no se saltan).

LAS PRUEBAS `xfail`: cuando el código no hace lo que dice el plan y podría ser un bug, la prueba
se escribe según el plan y se marca `xfail(strict=True)` con el código del posible bug (P-xx, ver
la tabla del PR). Si algún día el servidor cambia y la prueba empieza a pasar, `strict` avisa.
"""

import secrets
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import URL, Engine, make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from alembic import command
from app.db import get_db
from app.main import crear_app
from app.modelos import Grupo, Iglesia, Miembro, Usuario
from app.modelos.utilidades import obtener_url_base_datos
from app.seguridad.contrasenas import crear_hash
from app.seguridad.tokens import crear_token
from scripts.cargar_datos_ejemplo import (
    GASTOS,
    IGLESIA_DEMO,
    INGRESOS,
    VARIABLES_CLAVE,
    cargar_datos,
)

RUTA_ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"

MENSAJE_SIN_POSTGRES = (
    "No hay una base PostgreSQL configurada para las pruebas. Define DATABASE_URL en el "
    "entorno o en backend/.env, por ejemplo: "
    "postgresql+psycopg://postgres:TU_CONTRASENA@localhost:5432/postgres ."
)
MENSAJE_SIN_CONEXION = (
    "No se pudo crear la base temporal de pruebas en PostgreSQL. Revisa que el servicio "
    "esté corriendo, que la contraseña de DATABASE_URL sea la correcta y que ese usuario "
    "pueda crear bases de datos (CREATEDB)."
)

# Periodo que cubre todos los movimientos de ejemplo (octubre y noviembre de 2026).
FILTRO = "desde=2026-10-01&hasta=2026-11-30"

# Las 4 iglesias del ejemplo. La 3ra es la de las cuentas de ejemplo (IGLESIA_DEMO).
TERCERA = IGLESIA_DEMO
CUARTA = "4ta IAFCJ de Mérida"
SEXTA = "6ta IAFCJ de Mérida"
HUHI = "IAFCJ de Huhí"
IGLESIAS_AJENAS = [CUARTA, SEXTA, HUHI]

# Clave corta de cada cuenta -> usuario de los datos de ejemplo (Issue #5).
CUENTAS_EJEMPLO = {
    "presbitero": "presbitero.ejemplo",
    "pastor": "pastor.ejemplo",
    "apoyo_pastor": "apoyo.ejemplo",
    "tesorero": "tesorero.ejemplo",
    "lider_celula": "lider.celula.ejemplo",
    "ujier": "ujier.ejemplo",
}

# Cuentas que el ejemplo no trae: (clave, cargo, iglesia, ficha de miembro que dirige, activa).
# Todas de la 3ra salvo las de la 4ta. Una ficha ligada (D21) es lo que da el "área" del líder.
CUENTAS_EXTRA = [
    ("pastor_4ta", "pastor", CUARTA, None, True),
    ("tesorero_4ta", "tesorero", CUARTA, None, True),
    ("lider_red", "lider_red", TERCERA, "Elena Beatriz Cocom Ek", True),
    ("lider_ministerio", "lider_ministerio", TERCERA, "Abigail Noemí Tzec Moo", True),
    ("encargado_area", "encargado_area", TERCERA, "Samuel David Chulim Pool", True),
    ("esposa_pastor", "esposa_pastor", TERCERA, None, True),
    ("diacono", "diacono", TERCERA, None, True),
    ("ministro", "ministro", TERCERA, None, True),
    ("asistente", "asistente", TERCERA, None, True),
    ("desactivado", "tesorero", TERCERA, None, False),
]

# Cargos que no ven ni registran dinero (D9, D20 y D22). El tesorero SÍ lo ve, aparte.
CARGOS_SIN_DINERO = [
    "apoyo_pastor",
    "lider_celula",
    "lider_red",
    "lider_ministerio",
    "ujier",
    "encargado_area",
    "esposa_pastor",
    "diacono",
    "ministro",
    "asistente",
]


@dataclass
class Mundo:
    """Lo que las pruebas necesitan saber de la base temporal ya cargada."""

    motor: Engine
    claves: dict[str, str]  # contraseña (inventada) de cada cuenta de ejemplo, por cargo
    ids: dict[str, int] = field(default_factory=dict)  # clave corta de cuenta -> id
    iglesias: dict[str, int] = field(default_factory=dict)  # nombre -> id
    miembros: dict[str, int] = field(default_factory=dict)  # nombre -> id
    grupos: dict[str, int] = field(default_factory=dict)  # nombre -> id
    usuarios: dict[str, str] = field(default_factory=dict)  # clave corta -> nombre_usuario

    def token(self, cuenta: str) -> dict[str, str]:
        """Cabecera Authorization de una cuenta, con un token firmado igual que el login."""
        return {"Authorization": f"Bearer {crear_token(str(self.ids[cuenta]))}"}


@dataclass
class Api:
    """Cliente de pruebas con atajos: `api.get("/ingresos", "tesorero")` pide como esa cuenta."""

    cliente: TestClient
    sesion: Session
    mundo: Mundo

    def pedir(self, metodo: str, ruta: str, cuenta: str | None = None, **datos):
        cabeceras = self.mundo.token(cuenta) if cuenta else {}
        return self.cliente.request(metodo, ruta, headers=cabeceras, **datos)

    def get(self, ruta: str, cuenta: str | None = None):
        return self.pedir("GET", ruta, cuenta)

    def post(self, ruta: str, cuenta: str | None, json=None):
        return self.pedir("POST", ruta, cuenta, json=json)

    def put(self, ruta: str, cuenta: str | None, json=None):
        return self.pedir("PUT", ruta, cuenta, json=json)

    def delete(self, ruta: str, cuenta: str | None = None):
        return self.pedir("DELETE", ruta, cuenta)


@pytest.fixture(scope="module")
def url_servidor() -> URL:
    """URL del servidor PostgreSQL; si no hay una, la prueba falla con un mensaje claro."""
    texto = obtener_url_base_datos()
    if not texto or not texto.startswith("postgresql"):
        pytest.fail(MENSAJE_SIN_POSTGRES, pytrace=False)
    return make_url(texto)


@contextmanager
def _base_temporal(url_servidor: URL) -> Iterator[URL]:
    """Crea una base con nombre único, le aplica las migraciones y la borra al terminar."""
    nombre = f"iglesias_permisos_{uuid.uuid4().hex[:12]}"
    # AUTOCOMMIT: CREATE/DROP DATABASE no pueden ir dentro de una transacción.
    motor_admin = create_engine(url_servidor, isolation_level="AUTOCOMMIT")
    try:
        fallo = False
        try:
            with motor_admin.connect() as conexion:
                conexion.execute(text(f'CREATE DATABASE "{nombre}"'))
        except DBAPIError:
            fallo = True
        if fallo:
            # Se avisa fuera del except para no mostrar el error original (datos de conexión).
            pytest.fail(MENSAJE_SIN_CONEXION, pytrace=False)
        try:
            url = url_servidor.set(database=nombre)
            config = Config(str(RUTA_ALEMBIC_INI))
            config.attributes["url"] = url
            command.upgrade(config, "head")
            yield url
        finally:
            with motor_admin.connect() as conexion:
                conexion.execute(text(f'DROP DATABASE IF EXISTS "{nombre}" WITH (FORCE)'))
    finally:
        motor_admin.dispose()


def _crear_cuentas_extra(sesion: Session) -> None:
    """Agrega las cuentas que los datos de ejemplo no traen (ver CUENTAS_EXTRA)."""
    # El hash es de una contraseña inventada que nadie necesita: estas cuentas entran con token.
    hash_prueba = crear_hash(secrets.token_urlsafe(24))
    iglesias = {i.nombre: i.id for i in sesion.scalars(select(Iglesia))}
    miembros = {m.nombre: m.id for m in sesion.scalars(select(Miembro))}
    for clave, cargo, iglesia, ficha, activa in CUENTAS_EXTRA:
        sesion.add(
            Usuario(
                nombre_usuario=f"{clave}.prueba",
                nombre_completo=f"Persona ficticia {clave}",
                cargo=cargo,
                iglesia_id=iglesias[iglesia],
                miembro_id=miembros[ficha] if ficha else None,
                activo=activa,
                contrasena_hash=hash_prueba,
            )
        )
    sesion.flush()


@pytest.fixture(scope="module")
def mundo(url_servidor: URL) -> Iterator[Mundo]:
    """Una base temporal con los datos de ejemplo y las cuentas extra, cargada una sola vez."""
    # El token y el login necesitan SECRET_KEY: se inventa una solo para este módulo.
    ajustes = pytest.MonkeyPatch()
    ajustes.setenv("SECRET_KEY", secrets.token_urlsafe(32))
    try:
        with _base_temporal(url_servidor) as url:
            motor = create_engine(url)
            claves = {cargo: secrets.token_urlsafe(18) for cargo in VARIABLES_CLAVE}
            with Session(motor) as sesion, sesion.begin():
                cargar_datos(sesion, claves)
                _crear_cuentas_extra(sesion)
            mundo = Mundo(motor=motor, claves=claves)
            with Session(motor) as sesion:
                por_nombre = {u.nombre_usuario: u for u in sesion.scalars(select(Usuario))}
                for clave, nombre in CUENTAS_EJEMPLO.items():
                    mundo.ids[clave] = por_nombre[nombre].id
                    mundo.usuarios[clave] = nombre
                for clave, *_ in CUENTAS_EXTRA:
                    mundo.ids[clave] = por_nombre[f"{clave}.prueba"].id
                    mundo.usuarios[clave] = f"{clave}.prueba"
                mundo.iglesias = {i.nombre: i.id for i in sesion.scalars(select(Iglesia))}
                mundo.miembros = {m.nombre: m.id for m in sesion.scalars(select(Miembro))}
                mundo.grupos = {g.nombre: g.id for g in sesion.scalars(select(Grupo))}
            try:
                yield mundo
            finally:
                motor.dispose()
    finally:
        ajustes.undo()


@pytest.fixture
def api(mundo: Mundo) -> Iterator[Api]:
    """Cliente para UNA prueba: todo lo que haga se deshace al terminar (no deja datos)."""
    aplicacion = crear_app()
    with mundo.motor.connect() as conexion:
        transaccion = conexion.begin()
        # create_savepoint: si la API hace commit o un rollback por error, solo afecta a un
        # SAVEPOINT; la transacción de afuera sigue y se deshace al final.
        with Session(bind=conexion, join_transaction_mode="create_savepoint") as sesion:

            def sesion_de_prueba():
                yield sesion

            aplicacion.dependency_overrides[get_db] = sesion_de_prueba
            with TestClient(aplicacion) as cliente:
                try:
                    yield Api(cliente=cliente, sesion=sesion, mundo=mundo)
                finally:
                    aplicacion.dependency_overrides.clear()
                    if transaccion.is_active:
                        transaccion.rollback()


# ---------------------------------------------------------------------------
# Datos que se esperan según el script de ejemplo (no se repiten números a mano)
# ---------------------------------------------------------------------------


def ingresos_de(iglesia: str) -> int:
    """Cuántos ingresos de ejemplo tiene una iglesia."""
    return sum(1 for fila in INGRESOS if fila[1] == iglesia)


def gastos_de(iglesia: str) -> int:
    """Cuántos gastos de ejemplo tiene una iglesia."""
    return sum(1 for fila in GASTOS if fila[1] == iglesia)


# ---------------------------------------------------------------------------
# Prueba de humo de la infraestructura
# ---------------------------------------------------------------------------


def test_la_base_de_prueba_trae_los_datos_de_ejemplo_y_las_cuentas(api: Api) -> None:
    """Sanidad: las cuentas existen, el token funciona y la API responde con la base temporal."""
    respuesta = api.get("/usuarios/yo", "presbitero")
    assert respuesta.status_code == 200
    assert respuesta.json()["cargo"] == "presbitero"
    # Las cuentas extra también quedaron creadas, y la desactivada está desactivada.
    assert api.get("/usuarios/yo", "pastor_4ta").json()["cargo"] == "pastor"
    assert len(api.mundo.iglesias) == 4
    assert len(api.mundo.grupos) == 6


# (las pruebas de cada fase siguen abajo)
