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

import os
import secrets
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
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
from app.modelos import CARGOS, Gasto, Grupo, Iglesia, Ingreso, Miembro, Usuario
from app.modelos.utilidades import obtener_url_base_datos
from app.seguridad.contrasenas import crear_hash
from app.seguridad.tokens import crear_token
from scripts.cargar_datos_ejemplo import (
    GASTOS,
    GRUPOS,
    IGLESIA_DEMO,
    INGRESOS,
    INTEGRANTES,
    MIEMBROS,
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
    # Contraseña (inventada) de cada cuenta de ejemplo, por cargo, y la de la cuenta "desactivado".
    claves: dict[str, str]
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


def _crear_cuentas_extra(sesion: Session, clave_desactivada: str) -> None:
    """Agrega las cuentas que los datos de ejemplo no traen (ver CUENTAS_EXTRA).

    Las cuentas extra entran con token (no necesitan contraseña conocida), salvo la desactivada:
    su contraseña SÍ se conoce, para probar que ni con la contraseña correcta puede entrar.
    """
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
                contrasena_hash=crear_hash(clave_desactivada) if not activa else hash_prueba,
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
            # Contraseña (inventada) de la cuenta desactivada, para la prueba de login.
            claves["desactivado"] = secrets.token_urlsafe(18)
            with Session(motor) as sesion, sesion.begin():
                cargar_datos(sesion, claves)
                _crear_cuentas_extra(sesion, claves["desactivado"])
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


# ===========================================================================
# FASE 1: criterios de aceptación del Issue #10
# ===========================================================================

RECURSOS_DINERO = ["ingresos", "gastos"]


def esperados(recurso: str, iglesia: str | None = None) -> int:
    """Cuántos movimientos de ejemplo hay: de una iglesia o, sin iglesia, en total."""
    filas = INGRESOS if recurso == "ingresos" else GASTOS
    return sum(1 for fila in filas if iglesia is None or fila[1] == iglesia)


def listar_dinero(api: Api, recurso: str, cuenta: str, iglesia: str | None = None):
    """GET /ingresos o /gastos con el periodo del ejemplo y, si se pide, filtrando una iglesia."""
    ruta = f"/{recurso}?{FILTRO}"
    if iglesia is not None:
        ruta += f"&iglesia_id={api.mundo.iglesias[iglesia]}"
    return api.get(ruta, cuenta)


def cuerpo_dinero(recurso: str, iglesia_id: int) -> dict:
    """Cuerpo válido para registrar un ingreso o un gasto nuevo en esa iglesia."""
    if recurso == "ingresos":
        return {
            "iglesia_id": iglesia_id,
            "fecha": "2026-11-05",
            "culto": "culto_domingo",
            "partidas": [{"tipo": "diezmos", "monto": "10.50"}],
        }
    return {"iglesia_id": iglesia_id, "fecha": "2026-11-05", "categoria": "luz", "monto": "10.50"}


def un_movimiento_vigente(api: Api, recurso: str, iglesia: str) -> int:
    """Id de un ingreso o gasto de esa iglesia que todavía no está anulado."""
    modelo = Ingreso if recurso == "ingresos" else Gasto
    consulta = select(modelo.id).where(
        modelo.iglesia_id == api.mundo.iglesias[iglesia], modelo.anulado_en.is_(None)
    )
    return api.sesion.scalars(consulta.limit(1)).one()


def total_movimientos(api: Api, recurso: str) -> int:
    """Cuántos ingresos o gastos hay en la base (ve todo el presbítero)."""
    return len(listar_dinero(api, recurso, "presbitero").json())


# --- Criterio 1: el pastor de una iglesia no ve datos de otra; el presbítero ve todas ---


@pytest.mark.parametrize("recurso", RECURSOS_DINERO)
def test_pastor_ve_dinero_solo_de_su_iglesia(api: Api, recurso: str) -> None:
    """PERM-11: sin filtro y filtrando su iglesia, el pastor solo recibe movimientos de la suya."""
    propia = api.mundo.iglesias[TERCERA]
    for iglesia in (None, TERCERA):
        respuesta = listar_dinero(api, recurso, "pastor", iglesia)
        assert respuesta.status_code == 200
        filas = respuesta.json()
        assert len(filas) == esperados(recurso, TERCERA)
        assert {fila["iglesia_id"] for fila in filas} == {propia}


@pytest.mark.parametrize("recurso", RECURSOS_DINERO)
@pytest.mark.parametrize("ajena", IGLESIAS_AJENAS)
def test_pastor_no_ve_dinero_de_otra_iglesia(api: Api, recurso: str, ajena: str) -> None:
    """PERM-13: pedir el dinero de otra iglesia es 403, aunque se conozca el identificador."""
    assert listar_dinero(api, recurso, "pastor", ajena).status_code == 403


def test_pastor_de_la_4ta_no_ve_datos_de_la_6ta(api: Api) -> None:
    """Criterio del Issue: el pastor de la 4ta ve lo suyo y nada de la 6ta (dinero y personas)."""
    mundo = api.mundo
    cuarta, sexta = mundo.iglesias[CUARTA], mundo.iglesias[SEXTA]
    for recurso in RECURSOS_DINERO:
        propios = listar_dinero(api, recurso, "pastor_4ta", CUARTA)
        assert propios.status_code == 200
        assert len(propios.json()) == esperados(recurso, CUARTA)
        assert listar_dinero(api, recurso, "pastor_4ta", SEXTA).status_code == 403
    # Miembros: solo los de su iglesia. Si pide la 6ta, el servidor responde con la lista VACÍA
    # (200) en vez de 403: oculta que existan. El plan pedía 403 (ver tabla del PR, fila PERM-61).
    miembros = api.get("/miembros", "pastor_4ta").json()
    assert miembros and {m["iglesia_id"] for m in miembros} == {cuarta}
    assert api.get(f"/miembros?iglesia_id={sexta}", "pastor_4ta").json() == []
    de_la_6ta = mundo.miembros["Verónica Alejandra Ucán Dzul"]
    assert api.get(f"/miembros/{de_la_6ta}", "pastor_4ta").status_code == 404
    # Grupos: los del ejemplo son todos de la 3ra, así que el pastor de la 4ta no ve ninguno.
    assert api.get("/grupos", "pastor_4ta").json() == []
    celula = mundo.grupos["Célula Betania"]
    assert api.get(f"/grupos/{celula}", "pastor_4ta").status_code == 404
    assert api.get(f"/asignaciones/{celula}", "pastor_4ta").status_code == 403


@pytest.mark.parametrize("recurso", RECURSOS_DINERO)
def test_presbitero_ve_dinero_de_las_4_iglesias(api: Api, recurso: str) -> None:
    """PERM-16: el presbítero ve el dinero de cada iglesia y, sin filtro, el de todas."""
    todos = listar_dinero(api, recurso, "presbitero")
    assert todos.status_code == 200
    assert len(todos.json()) == esperados(recurso)
    assert {f["iglesia_id"] for f in todos.json()} == set(api.mundo.iglesias.values())
    for iglesia in (TERCERA, CUARTA, SEXTA, HUHI):
        una = listar_dinero(api, recurso, "presbitero", iglesia)
        assert una.status_code == 200
        assert len(una.json()) == esperados(recurso, iglesia)


def test_presbitero_ve_miembros_iglesias_y_grupos_de_todas(api: Api) -> None:
    """El presbítero ve todos los miembros, las 4 iglesias y todos los grupos."""
    assert len(api.get("/miembros", "presbitero").json()) == sum(len(v) for v in MIEMBROS.values())
    assert len(api.get("/iglesias", "presbitero").json()) == 4
    assert len(api.get("/grupos", "presbitero").json()) == len(GRUPOS)


def test_pastor_solo_ve_su_iglesia_en_la_lista_de_iglesias(api: Api) -> None:
    """El pastor (y cualquier cargo sin alcance total) recibe solo su iglesia en GET /iglesias."""
    for cuenta in ("pastor", "pastor_4ta", "tesorero", "lider_celula"):
        iglesias = api.get("/iglesias", cuenta).json()
        assert len(iglesias) == 1
    assert api.get("/iglesias", "pastor_4ta").json()[0]["nombre"] == CUARTA


# --- Criterio 2: el tesorero ve dinero solo de su iglesia; el líder y otros cargos, nada ---


@pytest.mark.parametrize("recurso", RECURSOS_DINERO)
def test_tesorero_ve_dinero_solo_de_su_iglesia(api: Api, recurso: str) -> None:
    """PERM-01, 03, 05 y 07: ve lo de su iglesia; lo de cualquier otra es 403."""
    propios = listar_dinero(api, recurso, "tesorero")
    assert propios.status_code == 200
    assert len(propios.json()) == esperados(recurso, TERCERA)
    assert {f["iglesia_id"] for f in propios.json()} == {api.mundo.iglesias[TERCERA]}
    for ajena in IGLESIAS_AJENAS:
        assert listar_dinero(api, recurso, "tesorero", ajena).status_code == 403


@pytest.mark.parametrize("recurso", RECURSOS_DINERO)
def test_tesorero_de_la_4ta_ve_solo_la_4ta(api: Api, recurso: str) -> None:
    """Lo mismo con un tesorero de otra iglesia: el aislamiento no depende de la 3ra."""
    propios = listar_dinero(api, recurso, "tesorero_4ta")
    assert len(propios.json()) == esperados(recurso, CUARTA)
    for ajena in (TERCERA, SEXTA, HUHI):
        assert listar_dinero(api, recurso, "tesorero_4ta", ajena).status_code == 403


@pytest.mark.parametrize("recurso", RECURSOS_DINERO)
def test_tesorero_registra_dinero_en_su_iglesia_y_no_en_otra(api: Api, recurso: str) -> None:
    """PERM-02, 04, 06 y 07: registra en la suya (201) y en cualquier otra recibe 403."""
    antes = total_movimientos(api, recurso)
    propia = api.mundo.iglesias[TERCERA]
    creado = api.post(f"/{recurso}", "tesorero", cuerpo_dinero(recurso, propia))
    assert creado.status_code == 201
    for ajena in IGLESIAS_AJENAS:
        rechazado = api.post(
            f"/{recurso}", "tesorero", cuerpo_dinero(recurso, api.mundo.iglesias[ajena])
        )
        assert rechazado.status_code == 403
    # Solo se guardó el de su iglesia (la respuesta de ingresos es una lista de partidas).
    assert total_movimientos(api, recurso) == antes + 1


# Quién puede anular y dónde: (cuenta, iglesia del movimiento, código esperado). PERM-10, 14, 18.
ANULACIONES = [
    ("tesorero", TERCERA, 200),
    ("tesorero", CUARTA, 403),
    ("pastor", TERCERA, 200),
    ("pastor", SEXTA, 403),
    ("presbitero", TERCERA, 200),
    ("presbitero", CUARTA, 200),
    ("presbitero", HUHI, 200),
    ("tesorero_4ta", CUARTA, 200),
    ("tesorero_4ta", TERCERA, 403),
]


@pytest.mark.parametrize("recurso", RECURSOS_DINERO)
@pytest.mark.parametrize(("cuenta", "iglesia", "codigo"), ANULACIONES)
def test_quien_anula_dinero_y_donde(
    api: Api, recurso: str, cuenta: str, iglesia: str, codigo: int
) -> None:
    """El tesorero y el pastor anulan solo en su iglesia; el presbítero, en cualquiera."""
    identificador = un_movimiento_vigente(api, recurso, iglesia)
    respuesta = api.post(
        f"/{recurso}/{identificador}/anular", cuenta, {"motivo": "Prueba de permisos"}
    )
    assert respuesta.status_code == codigo
    if codigo == 200:
        assert respuesta.json()["anulado"] is True
        assert respuesta.json()["motivo_anulacion"] == "Prueba de permisos"


@pytest.mark.parametrize("recurso", RECURSOS_DINERO)
@pytest.mark.parametrize("cuenta", ["presbitero", "pastor", "tesorero"])
def test_nadie_borra_ingresos_ni_gastos(api: Api, recurso: str, cuenta: str) -> None:
    """PERM-28 (corregido): no existe ruta de borrado, así que DELETE da 404 y nada se pierde.

    El plan decía 403; lo que importa (que no se borre) se cumple porque la ruta no existe.
    """
    antes = total_movimientos(api, recurso)
    identificador = un_movimiento_vigente(api, recurso, TERCERA)
    assert api.delete(f"/{recurso}/{identificador}", cuenta).status_code == 404
    assert total_movimientos(api, recurso) == antes


@pytest.mark.parametrize("recurso", RECURSOS_DINERO)
@pytest.mark.parametrize("cuenta", CARGOS_SIN_DINERO)
def test_cargos_sin_dinero_reciben_403(api: Api, recurso: str, cuenta: str) -> None:
    """PERM-19 a 27 (D9, D20 y D22): apoyo, líderes, ujier y otros cargos no tocan el dinero."""
    identificador = un_movimiento_vigente(api, recurso, TERCERA)
    propia = api.mundo.iglesias[TERCERA]
    assert listar_dinero(api, recurso, cuenta).status_code == 403
    assert api.post(f"/{recurso}", cuenta, cuerpo_dinero(recurso, propia)).status_code == 403
    anular = api.post(f"/{recurso}/{identificador}/anular", cuenta, {"motivo": "Prueba"})
    assert anular.status_code == 403


def test_el_tesorero_no_ve_miembros_ni_grupos(api: Api) -> None:
    """PERM-69 y 100 (D20): el tesorero maneja dinero, no datos personales ni grupos."""
    for ruta in ("/miembros", "/grupos", "/asignaciones/grupos"):
        assert api.get(ruta, "tesorero").status_code == 403


def test_los_ingresos_no_registran_quien_dio(api: Api) -> None:
    """PERM-30 y 32 (D17): ningún ingreso trae datos de persona ni acepta un donante."""
    filas = listar_dinero(api, "ingresos", "presbitero").json()
    campos = {
        "id",
        "iglesia_id",
        "iglesia_nombre",
        "fecha",
        "culto",
        "tipo",
        "monto",
        "descripcion",
        "anulado",
        "motivo_anulacion",
    }
    assert all(set(fila) == campos for fila in filas)
    antes = total_movimientos(api, "ingresos")
    cuerpo = cuerpo_dinero("ingresos", api.mundo.iglesias[TERCERA])
    cuerpo["miembro_id"] = api.mundo.miembros["Marta Elena Canul Pech"]
    rechazado = api.post("/ingresos", "tesorero", cuerpo)
    assert rechazado.status_code == 422  # el dato no se acepta (no es un 403)
    assert total_movimientos(api, "ingresos") == antes


# --- Criterio 3: un líder solo ve su grupo ---

# Cada líder dirige UN grupo en los datos de ejemplo (D21: el área sale de los grupos que dirige).
GRUPO_DEL_LIDER = {
    "lider_celula": "Célula Betania",
    "lider_red": "Red de Damas",
    "lider_ministerio": "Ministerio de Alabanza",
    "encargado_area": "Tiendita",
}


def _datos_de_grupo(api: Api, nombre: str) -> dict:
    """Cuerpo válido de PUT /grupos para dejar un grupo del ejemplo tal como está."""
    tipo, _, lider, asistente = next(g for g in GRUPOS if g[1] == nombre)
    miembros = api.mundo.miembros
    return {
        "nombre": nombre,
        "tipo": tipo,
        "iglesia_id": api.mundo.iglesias[TERCERA],
        "lider_id": miembros[lider],
        "asistente_id": miembros[asistente] if asistente else None,
    }


@pytest.mark.parametrize(("cuenta", "propio"), sorted(GRUPO_DEL_LIDER.items()))
def test_un_lider_solo_ve_su_grupo(api: Api, cuenta: str, propio: str) -> None:
    """PERM-93, 94 y 66: ve únicamente el grupo que dirige; los demás no existen para él."""
    grupos = api.mundo.grupos
    for ruta in ("/grupos", "/asignaciones/grupos"):
        visibles = api.get(ruta, cuenta).json()
        assert [g["nombre"] for g in visibles] == [propio]
    assert api.get(f"/grupos/{grupos[propio]}", cuenta).status_code == 200
    assert api.get(f"/asignaciones/{grupos[propio]}", cuenta).status_code == 200
    for nombre, identificador in grupos.items():
        if nombre != propio:
            # Un grupo ajeno: 404 al verlo como grupo y 403 al pedir sus integrantes.
            assert api.get(f"/grupos/{identificador}", cuenta).status_code == 404
            assert api.get(f"/asignaciones/{identificador}", cuenta).status_code == 403


def test_el_lider_de_celula_solo_ve_los_miembros_de_su_celula(api: Api) -> None:
    """PERM-65 y 66: ve a los integrantes de su célula; cualquier otro miembro no existe para él.

    El plan pedía 403 al consultar un miembro ajeno; el servidor responde 404 (oculta que existe).
    """
    miembros = api.mundo.miembros
    _, nombre, lider, asistente = next(g for g in GRUPOS if g[0] == "celula")
    de_la_celula = {lider, asistente, *INTEGRANTES[nombre]}
    visibles = {m["id"] for m in api.get("/miembros", "lider_celula").json()}
    assert visibles == {miembros[n] for n in de_la_celula}
    for n, identificador in miembros.items():
        esperado = 200 if n in de_la_celula else 404
        assert api.get(f"/miembros/{identificador}", "lider_celula").status_code == esperado


def test_el_lider_no_registra_miembros(api: Api) -> None:
    """PERM-67: un líder consulta a su grupo, pero no registra miembros."""
    cuerpo = {
        "iglesia_id": api.mundo.iglesias[TERCERA],
        "nombre": "Persona ficticia",
        "estado": "activo",
    }
    for cuenta in ("lider_celula", "lider_red", "lider_ministerio"):
        assert api.post("/miembros", cuenta, cuerpo).status_code == 403


def test_el_lider_edita_su_grupo_y_no_otro(api: Api) -> None:
    """PERM-97 y 98: el líder edita el grupo que dirige; el de otro no existe para él (404)."""
    celula = api.mundo.grupos["Célula Betania"]
    propio = api.put(f"/grupos/{celula}", "lider_celula", _datos_de_grupo(api, "Célula Betania"))
    assert propio.status_code == 200
    ajeno = api.mundo.grupos["Red de Damas"]
    datos_ajenos = _datos_de_grupo(api, "Red de Damas")
    assert api.put(f"/grupos/{ajeno}", "lider_celula", datos_ajenos).status_code == 404


def test_el_lider_quita_integrantes_de_su_grupo_y_no_de_otro(api: Api) -> None:
    """PERM-95 (quitar) y 96: quita del grupo que dirige (204); en otro grupo recibe 403."""
    miembros, grupos = api.mundo.miembros, api.mundo.grupos
    carlos = miembros["Carlos Alberto Dzul Uc"]
    assert (
        api.delete(f"/asignaciones/{grupos['Célula Betania']}/{carlos}", "lider_celula").status_code
        == 204
    )
    sofia = miembros["Sofía Guadalupe Euán Cauich"]
    ajeno = api.delete(f"/asignaciones/{grupos['Ministerio de Alabanza']}/{sofia}", "lider_celula")
    assert ajeno.status_code == 403


@pytest.mark.xfail(
    strict=True,
    reason=(
        "P-1: el plan (PERM-95, #22) dice que el líder asigna miembros a su grupo; el servidor "
        "solo deja asignar a presbítero, pastor y apoyo (el líder solo puede quitar). Es una "
        "decisión de Marcos: o se cambia la regla o se corrige el plan."
    ),
)
def test_el_lider_asigna_miembros_a_su_grupo(api: Api) -> None:
    """PERM-95 (asignar): el líder agrega un miembro a su propio grupo (plan: permitido)."""
    visitante = api.mundo.miembros["Ricardo Iván Ay Sosa"]
    celula = api.mundo.grupos["Célula Betania"]
    respuesta = api.post(
        "/asignaciones", "lider_celula", {"grupo_id": celula, "miembro_id": visitante}
    )
    assert respuesta.status_code == 201


def test_el_lider_no_asigna_miembros_a_otro_grupo(api: Api) -> None:
    """PERM-96 (asignar): en un grupo ajeno el líder recibe 403."""
    visitante = api.mundo.miembros["Ricardo Iván Ay Sosa"]
    ajeno = api.mundo.grupos["Red de Damas"]
    respuesta = api.post(
        "/asignaciones", "lider_celula", {"grupo_id": ajeno, "miembro_id": visitante}
    )
    assert respuesta.status_code == 403


# ===========================================================================
# FASE 2: escalamiento de cargos al crear y editar usuarios (D19 y D20)
# ===========================================================================
# Regla: nadie crea ni asigna un cargo con más acceso al dinero del que tiene. El apoyo solo
# crea cargos sin dinero; el pastor crea al tesorero de su iglesia; solo el presbítero crea
# pastores; nadie crea presbíteros desde la app; nadie, salvo el presbítero, cambia su cargo.

# Cargos con los que el apoyo SÍ puede crear cuentas (PERM-48a): ninguno ve dinero.
CARGOS_QUE_CREA_EL_APOYO = [
    "lider_celula",
    "lider_red",
    "lider_ministerio",
    "ujier",
    "diacono",
    "ministro",
    "encargado_area",
    "esposa_pastor",
    "asistente",
]
# Cargos con los que el pastor SÍ puede crear cuentas (todos menos pastor y presbítero).
CARGOS_QUE_CREA_EL_PASTOR = [c for c in CARGOS if c not in ("pastor", "presbitero")]
# Cuentas que no administran usuarios: todo POST o GET de usuarios les da 403.
CUENTAS_SIN_GESTION_DE_USUARIOS = [
    "tesorero",
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


def cuenta_nueva(iglesia_id: int | None, cargo: str) -> dict:
    """Cuerpo de POST /usuarios con datos inventados (la contraseña se inventa y no se imprime)."""
    return {
        "nombre_usuario": f"nueva.{uuid.uuid4().hex[:10]}",
        "nombre_completo": "Persona ficticia",
        "cargo": cargo,
        "iglesia_id": iglesia_id,
        "contrasena": secrets.token_urlsafe(14),
    }


def cambios_de(api: Api, cuenta: str, **cambios) -> dict:
    """Cuerpo de PUT /usuarios con los datos actuales de la cuenta y los cambios indicados."""
    actual = api.sesion.get(Usuario, api.mundo.ids[cuenta])
    base = {
        "nombre_completo": actual.nombre_completo,
        "cargo": actual.cargo,
        "iglesia_id": actual.iglesia_id,
        "activo": actual.activo,
    }
    return {**base, **cambios}


@pytest.mark.parametrize("iglesia", [TERCERA, CUARTA, SEXTA, HUHI])
@pytest.mark.parametrize("cargo", ["pastor", "tesorero", "ujier"])
def test_el_presbitero_crea_usuarios_en_cualquier_iglesia(
    api: Api, iglesia: str, cargo: str
) -> None:
    """PERM-46 y 46a: el presbítero crea cuentas en cualquier iglesia, también pastores."""
    cuerpo = cuenta_nueva(api.mundo.iglesias[iglesia], cargo)
    respuesta = api.post("/usuarios", "presbitero", cuerpo)
    assert respuesta.status_code == 201
    assert respuesta.json()["cargo"] == cargo
    # La respuesta nunca devuelve la contraseña ni su hash.
    assert cuerpo["contrasena"] not in respuesta.text
    assert "hash" not in respuesta.text and "contrasena" not in respuesta.json()


def test_nadie_crea_presbiteros_desde_la_app(api: Api) -> None:
    """PERM-51a y D20 (7): ni el presbítero, ni el pastor, ni el apoyo crean un presbítero."""
    for cuenta in ("presbitero", "pastor", "apoyo_pastor"):
        cuerpo = cuenta_nueva(
            None if cuenta == "presbitero" else api.mundo.iglesias[TERCERA], "presbitero"
        )
        assert api.post("/usuarios", cuenta, cuerpo).status_code == 403


@pytest.mark.parametrize("cargo", CARGOS_QUE_CREA_EL_PASTOR)
def test_el_pastor_crea_cuentas_de_su_iglesia(api: Api, cargo: str) -> None:
    """PERM-47 y 53: con todos los cargos menos pastor y presbítero; incluye al tesorero."""
    cuerpo = cuenta_nueva(api.mundo.iglesias[TERCERA], cargo)
    respuesta = api.post("/usuarios", "pastor", cuerpo)
    assert respuesta.status_code == 201
    assert respuesta.json()["iglesia_id"] == api.mundo.iglesias[TERCERA]


@pytest.mark.parametrize("cargo", CARGOS_QUE_CREA_EL_APOYO)
def test_el_apoyo_crea_cuentas_sin_acceso_al_dinero(api: Api, cargo: str) -> None:
    """PERM-48 y 48a (D19): el apoyo crea solo cargos que no ven dinero."""
    cuerpo = cuenta_nueva(api.mundo.iglesias[TERCERA], cargo)
    assert api.post("/usuarios", "apoyo_pastor", cuerpo).status_code == 201


@pytest.mark.parametrize("cargo", ["tesorero", "pastor", "presbitero"])
def test_el_apoyo_no_crea_cargos_con_dinero_ni_pastores(api: Api, cargo: str) -> None:
    """PERM-52 y 52a (D19): nadie obtiene más dinero por otra cuenta; el apoyo recibe 403."""
    cuerpo = cuenta_nueva(api.mundo.iglesias[TERCERA], cargo)
    assert api.post("/usuarios", "apoyo_pastor", cuerpo).status_code == 403


@pytest.mark.parametrize("cargo", ["pastor", "presbitero"])
def test_el_pastor_no_crea_pastores_ni_presbiteros(api: Api, cargo: str) -> None:
    """PERM-51 y 51a (D19): solo el presbítero crea pastores."""
    cuerpo = cuenta_nueva(api.mundo.iglesias[TERCERA], cargo)
    assert api.post("/usuarios", "pastor", cuerpo).status_code == 403


@pytest.mark.parametrize("cuenta", ["pastor", "apoyo_pastor"])
@pytest.mark.parametrize("ajena", IGLESIAS_AJENAS)
@pytest.mark.parametrize("cargo", ["ujier", "tesorero"])
def test_pastor_y_apoyo_no_crean_cuentas_en_otra_iglesia(
    api: Api, cuenta: str, ajena: str, cargo: str
) -> None:
    """PERM-49 y 53a: solo dentro de su iglesia, aunque el cargo en sí esté permitido."""
    cuerpo = cuenta_nueva(api.mundo.iglesias[ajena], cargo)
    assert api.post("/usuarios", cuenta, cuerpo).status_code == 403


@pytest.mark.parametrize("cuenta", CUENTAS_SIN_GESTION_DE_USUARIOS)
def test_cuentas_sin_gestion_no_crean_ni_consultan_usuarios(api: Api, cuenta: str) -> None:
    """PERM-50 y 56: solo presbítero, pastor y apoyo administran cuentas; los demás, 403."""
    cuerpo = cuenta_nueva(api.mundo.iglesias[TERCERA], "ujier")
    assert api.post("/usuarios", cuenta, cuerpo).status_code == 403
    assert api.get("/usuarios", cuenta).status_code == 403
    assert api.get(f"/usuarios/{api.mundo.ids['ujier']}", cuenta).status_code == 403


@pytest.mark.parametrize("nuevo_cargo", ["lider_celula", "tesorero", "pastor"])
def test_el_apoyo_no_cambia_su_propio_cargo(api: Api, nuevo_cargo: str) -> None:
    """PERM-52b: el apoyo no se sube de cargo. Editar su nombre (mismo cargo) sí se permite."""
    identificador = api.mundo.ids["apoyo_pastor"]
    cambio = cambios_de(api, "apoyo_pastor", cargo=nuevo_cargo)
    assert api.put(f"/usuarios/{identificador}", "apoyo_pastor", cambio).status_code == 403
    mismo_cargo = cambios_de(api, "apoyo_pastor", nombre_completo="Nombre nuevo ficticio")
    assert api.put(f"/usuarios/{identificador}", "apoyo_pastor", mismo_cargo).status_code == 200


@pytest.mark.parametrize("nuevo_cargo", ["tesorero", "pastor"])
def test_el_apoyo_no_sube_a_otro_a_tesorero_ni_pastor(api: Api, nuevo_cargo: str) -> None:
    """PERM-52c (D19): tampoco cambiando el cargo de una cuenta que ya existe."""
    identificador = api.mundo.ids["ujier"]
    cambio = cambios_de(api, "ujier", cargo=nuevo_cargo)
    assert api.put(f"/usuarios/{identificador}", "apoyo_pastor", cambio).status_code == 403


@pytest.mark.parametrize("nuevo_cargo", ["presbitero", "pastor"])
def test_el_pastor_no_sube_a_otro_a_presbitero_ni_pastor(api: Api, nuevo_cargo: str) -> None:
    """PERM-51b (D19): el pastor tampoco asciende cuentas a presbítero o pastor."""
    identificador = api.mundo.ids["ujier"]
    cambio = cambios_de(api, "ujier", cargo=nuevo_cargo)
    assert api.put(f"/usuarios/{identificador}", "pastor", cambio).status_code == 403


def test_el_pastor_si_sube_a_otro_a_tesorero(api: Api) -> None:
    """PERM-53 (por edición): el pastor puede dar el cargo de tesorero en su iglesia."""
    identificador = api.mundo.ids["ujier"]
    cambio = cambios_de(api, "ujier", cargo="tesorero")
    respuesta = api.put(f"/usuarios/{identificador}", "pastor", cambio)
    assert respuesta.status_code == 200
    assert respuesta.json()["cargo"] == "tesorero"


@pytest.mark.parametrize("cuenta", ["pastor", "apoyo_pastor", "tesorero", "lider_celula", "ujier"])
def test_nadie_salvo_el_presbitero_cambia_su_propio_cargo(api: Api, cuenta: str) -> None:
    """PERM-57 (D20, 8): ni el pastor ni los demás cargos se asignan otro cargo a sí mismos."""
    identificador = api.mundo.ids[cuenta]
    for nuevo_cargo in ("tesorero", "pastor", "presbitero"):
        if nuevo_cargo == api.sesion.get(Usuario, identificador).cargo:
            continue
        cambio = cambios_de(api, cuenta, cargo=nuevo_cargo)
        assert api.put(f"/usuarios/{identificador}", cuenta, cambio).status_code == 403


def test_nadie_promueve_a_presbitero_desde_la_app(api: Api) -> None:
    """D20 (7): ni siquiera el presbítero convierte a otra cuenta en presbítero."""
    identificador = api.mundo.ids["ujier"]
    cambio = cambios_de(api, "ujier", cargo="presbitero", iglesia_id=None)
    assert api.put(f"/usuarios/{identificador}", "presbitero", cambio).status_code == 403


def test_pastor_y_apoyo_solo_ven_las_cuentas_de_su_iglesia(api: Api) -> None:
    """PERM-54 y 55: la lista trae solo su iglesia; una cuenta de otra iglesia es 403."""
    propia = api.mundo.iglesias[TERCERA]
    de_la_4ta = api.mundo.ids["pastor_4ta"]
    for cuenta in ("pastor", "apoyo_pastor"):
        lista = api.get("/usuarios", cuenta).json()
        assert lista and {fila["iglesia_id"] for fila in lista} == {propia}
        assert api.get(f"/usuarios/{de_la_4ta}", cuenta).status_code == 403
        cambio = cambios_de(api, "pastor_4ta", activo=False)
        assert api.put(f"/usuarios/{de_la_4ta}", cuenta, cambio).status_code == 403
    # El presbítero, en cambio, ve las cuentas de todas las iglesias.
    todas = api.get("/usuarios", "presbitero").json()
    assert {propia, api.mundo.iglesias[CUARTA]} <= {fila["iglesia_id"] for fila in todas}


def test_desactivar_una_cuenta_le_quita_el_acceso(api: Api) -> None:
    """PERM-54 y EXTRA-06: el pastor desactiva al ujier y su sesión deja de valer (401)."""
    assert api.get("/usuarios/yo", "ujier").status_code == 200
    identificador = api.mundo.ids["ujier"]
    cambio = cambios_de(api, "ujier", activo=False)
    assert api.put(f"/usuarios/{identificador}", "pastor", cambio).status_code == 200
    assert api.get("/usuarios/yo", "ujier").status_code == 401


def test_el_apoyo_no_toca_cuentas_con_acceso_al_dinero(api: Api) -> None:
    """Consecuencia de D19 (no está en el plan): el apoyo no edita ni desactiva al tesorero.

    Si pudiera, desactivarlo o cambiarle datos le daría control indirecto sobre el dinero. El
    pastor sí puede.
    """
    identificador = api.mundo.ids["tesorero"]
    cambio = cambios_de(api, "tesorero", activo=False)
    assert api.put(f"/usuarios/{identificador}", "apoyo_pastor", cambio).status_code == 403
    assert api.put(f"/usuarios/{identificador}", "pastor", cambio).status_code == 200


# ===========================================================================
# FASE 3: sin sesión, token malo, credenciales incorrectas y cuenta desactivada
# ===========================================================================

# Rutas protegidas de cada módulo (todo lo que no sea horarios y ubicaciones exige sesión).
RUTAS_PROTEGIDAS = [
    "/usuarios",
    "/usuarios/yo",
    "/miembros",
    "/grupos",
    f"/ingresos?{FILTRO}",
    f"/gastos?{FILTRO}",
    "/asistencia",
    "/menores",
    "/asignaciones/grupos",
    "/eventos",
    "/comunicados",
    "/iglesias",
    "/sedes",
]
MENSAJE_SESION_INVALIDA = "Sesión no válida o vencida"


@pytest.mark.parametrize("ruta", RUTAS_PROTEGIDAS)
def test_sin_sesion_toda_ruta_protegida_da_401(api: Api, ruta: str) -> None:
    """EXTRA-01: sin Authorization, ningún módulo protegido responde datos."""
    respuesta = api.get(ruta)
    assert respuesta.status_code == 401
    assert respuesta.json() == {"detail": MENSAJE_SESION_INVALIDA}
    assert respuesta.headers["WWW-Authenticate"] == "Bearer"


def test_sin_sesion_se_ven_horarios_y_ubicaciones_y_nada_mas(api: Api) -> None:
    """EXTRA-02 (D10): lo público es solo la ficha de cada iglesia con sus sedes y horarios."""
    respuesta = api.get("/publico/iglesias")
    assert respuesta.status_code == 200
    iglesias = respuesta.json()
    assert len(iglesias) == 4
    campos = {"id", "nombre", "pastor", "foto_url", "telefono_iglesia", "redes", "sedes"}
    assert all(set(fila) == campos for fila in iglesias)
    # Nada de dinero ni de personas en lo público.
    assert "monto" not in respuesta.text and "miembro" not in respuesta.text
    assert api.get("/salud").status_code == 200


def _token_malo(modo: str, usuario_id: int) -> str:
    """Un token que NO debe aceptarse, armado con la misma SECRET_KEY de la prueba."""
    clave = os.environ["SECRET_KEY"]
    ahora = datetime.now(UTC)
    contenido = {"sub": str(usuario_id), "iat": ahora, "exp": ahora + timedelta(minutes=30)}
    firma, algoritmo = clave, "HS256"
    if modo == "vencido":
        contenido["iat"], contenido["exp"] = (
            ahora - timedelta(hours=1),
            ahora - timedelta(minutes=30),
        )
    elif modo == "otra_clave":
        firma = secrets.token_urlsafe(32)
    elif modo == "sin_exp":
        contenido.pop("exp")
    elif modo == "algoritmo":
        firma, algoritmo = secrets.token_urlsafe(48), "HS384"
    elif modo == "usuario_inexistente":
        contenido["sub"] = "99999999"
    elif modo == "sujeto_no_numerico":
        contenido["sub"] = "no-es-un-numero"
    token = jwt.encode(contenido, firma, algorithm=algoritmo)
    if modo == "alterado":
        cabecera, datos, firma_token = token.split(".")
        token = f"{cabecera}.{datos}.{'A' if firma_token[0] != 'A' else 'B'}{firma_token[1:]}"
    return token


@pytest.mark.parametrize(
    "modo",
    [
        "vencido",
        "alterado",
        "otra_clave",
        "sin_exp",
        "algoritmo",
        "usuario_inexistente",
        "sujeto_no_numerico",
    ],
)
def test_un_token_vencido_o_alterado_da_401(api: Api, modo: str) -> None:
    """EXTRA-03: ni el token vencido, ni el alterado, ni el de otra clave abren nada."""
    token = _token_malo(modo, api.mundo.ids["presbitero"])
    for ruta in ("/usuarios/yo", f"/ingresos?{FILTRO}"):
        respuesta = api.cliente.get(ruta, headers={"Authorization": f"Bearer {token}"})
        assert respuesta.status_code == 401
        assert token not in respuesta.text


def test_credenciales_incorrectas_dan_el_mismo_401_sin_revelar_cual_fallo(api: Api) -> None:
    """EXTRA-04: con la contraseña buena entra; con una mala o un usuario falso, mismo mensaje."""
    usuario = api.mundo.usuarios["pastor"]
    clave = api.mundo.claves["pastor"]
    entra = api.cliente.post("/auth/login", json={"usuario": usuario, "contrasena": clave})
    assert entra.status_code == 200 and entra.json()["token_type"] == "bearer"
    # El token que entrega el login abre la sesión de esa cuenta.
    cabecera = {"Authorization": f"Bearer {entra.json()['access_token']}"}
    assert api.cliente.get("/usuarios/yo", headers=cabecera).json()["cargo"] == "pastor"

    mala = api.cliente.post(
        "/auth/login", json={"usuario": usuario, "contrasena": "otra-clave-xyz"}
    )
    falso = api.cliente.post("/auth/login", json={"usuario": "no.existe", "contrasena": clave})
    assert mala.status_code == falso.status_code == 401
    assert mala.json() == falso.json()  # no dice si falló el usuario o la contraseña
    assert clave not in mala.text + falso.text


def test_una_cuenta_desactivada_no_inicia_sesion_ni_con_la_contraseña_correcta(api: Api) -> None:
    """EXTRA-05: el login la rechaza con el mismo 401 de cualquier error de credenciales."""
    respuesta = api.cliente.post(
        "/auth/login",
        json={
            "usuario": api.mundo.usuarios["desactivado"],
            "contrasena": api.mundo.claves["desactivado"],
        },
    )
    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == "Usuario o contraseña incorrectos."


def test_una_cuenta_desactivada_con_token_valido_no_entra(api: Api) -> None:
    """EXTRA-06: aunque conserve un token firmado, el servidor consulta la cuenta y da 401."""
    for ruta in ("/usuarios/yo", f"/ingresos?{FILTRO}"):
        assert api.get(ruta, "desactivado").status_code == 401
