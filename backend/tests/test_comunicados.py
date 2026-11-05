"""API de comunicados contra un PostgreSQL temporal migrado con Alembic (Issue #33, D9 y D20).

Todos los nombres, cargos y textos son inventados.
"""

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from alembic import command
from app.db import get_db
from app.main import crear_app
from app.modelos import Comunicado, Iglesia, Usuario
from app.modelos.utilidades import obtener_url_base_datos
from app.modulos.comunicados.servicio import hoy_en_merida
from app.seguridad.contrasenas import crear_hash
from app.seguridad.tokens import crear_token

HOY = hoy_en_merida()
MANANA = HOY + timedelta(days=1)
AYER = HOY - timedelta(days=1)

MENSAJES = {
    "titulo": "Escribe un título de 1 a 150 letras.",
    "contenido": "Escribe el contenido del comunicado (hasta 5000 letras).",
    "vigente_hasta": "Escribe una fecha de vigencia válida.",
}


@pytest.fixture(scope="module")
def motor():
    """Crea y borra su propia base temporal; nunca migra la base configurada."""
    url_texto = obtener_url_base_datos()
    if not url_texto or not url_texto.startswith("postgresql"):
        pytest.fail(
            "Las pruebas de comunicados requieren DATABASE_URL de PostgreSQL.", pytrace=False
        )
    url = make_url(url_texto)
    nombre = f"iglesias_comunicados_{uuid.uuid4().hex[:12]}"
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    creado = False
    try:
        try:
            with admin.connect() as conexion:
                conexion.execute(text(f'CREATE DATABASE "{nombre}"'))
            creado = True
        except DBAPIError:
            pytest.fail("No se pudo crear la base temporal; revisa PostgreSQL.", pytrace=False)
        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        config.attributes["url"] = url.set(database=nombre)
        motor = create_engine(url.set(database=nombre))
        try:
            command.upgrade(config, "head")
            yield motor
        finally:
            motor.dispose()
    finally:
        if creado:
            with admin.connect() as conexion:
                conexion.execute(text(f'DROP DATABASE "{nombre}" WITH (FORCE)'))
        admin.dispose()


@pytest.fixture
def sesion(motor):
    """Cada prueba trabaja en una transacción que se deshace al terminar."""
    with motor.connect() as conexion:
        transaccion = conexion.begin()
        with Session(bind=conexion) as s:
            try:
                yield s
            finally:
                if transaccion.is_active:
                    transaccion.rollback()


@pytest.fixture
def mundo(sesion, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", secrets.token_urlsafe(32))
    cuarta = Iglesia(nombre="4ta IAFCJ de Mérida")
    sexta = Iglesia(nombre="6ta IAFCJ de Mérida")
    sesion.add_all([cuarta, sexta])
    sesion.flush()

    def cuenta(usuario, cargo, iglesia, activo=True):
        fila = Usuario(
            nombre_usuario=usuario,
            nombre_completo=f"Persona {usuario}",
            contrasena_hash=crear_hash(secrets.token_urlsafe(16)),
            cargo=cargo,
            iglesia_id=iglesia.id if iglesia else None,
            activo=activo,
        )
        sesion.add(fila)
        sesion.flush()
        return fila

    cuentas = {
        "presbitero": cuenta("presbitero.a", "presbitero", None),
        "pastor4": cuenta("pastor.cuarta", "pastor", cuarta),
        "apoyo4": cuenta("apoyo.cuarta", "apoyo_pastor", cuarta),
        "pastor6": cuenta("pastor.sexta", "pastor", sexta),
        "tesorero4": cuenta("tesorero.cuarta", "tesorero", cuarta),
        "lider4": cuenta("lider.cuarta", "lider_celula", cuarta),
        "baja4": cuenta("pastor.baja", "pastor", cuarta, activo=False),
    }
    return {"cuarta": cuarta, "sexta": sexta, "cuentas": cuentas}


@pytest.fixture
def cliente(sesion, mundo):
    aplicacion = crear_app()

    def sesion_prueba():
        yield sesion

    aplicacion.dependency_overrides[get_db] = sesion_prueba
    with TestClient(aplicacion) as c:
        yield c
    aplicacion.dependency_overrides.clear()


def cabecera(mundo, quien):
    return {"Authorization": f"Bearer {crear_token(str(mundo['cuentas'][quien].id))}"}


def cuerpo(iglesia_id=None, **cambios):
    base = {"titulo": "Retiro de damas", "contenido": "Será el sábado.", "vigente_hasta": MANANA}
    datos = base | cambios
    datos["vigente_hasta"] = str(datos["vigente_hasta"])
    return datos | {"iglesia_id": iglesia_id}


def publicar(cliente, mundo, quien, **kwargs):
    respuesta = cliente.post("/comunicados", json=cuerpo(**kwargs), headers=cabecera(mundo, quien))
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def vencido(sesion, mundo, titulo="Ya venció", iglesia=None):
    """Un comunicado publicado hace 10 días que venció ayer (se inserta directo)."""
    fila = Comunicado(
        titulo=titulo,
        contenido="Texto viejo.",
        iglesia_id=iglesia.id if iglesia else None,
        publicado_en=datetime.now(UTC) - timedelta(days=10),
        vigente_hasta=AYER,
        creado_por=mundo["cuentas"]["presbitero"].id,
    )
    sesion.add(fila)
    sesion.flush()
    return fila


# ---- Sesión -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("metodo", "ruta"),
    [
        ("get", "/comunicados"),
        ("get", "/comunicados/1"),
        ("post", "/comunicados"),
        ("put", "/comunicados/1"),
    ],
)
def test_sin_sesion_da_401(cliente, metodo, ruta):
    assert getattr(cliente, metodo)(ruta).status_code == 401


def test_cuenta_desactivada_con_token_valido_da_401(cliente, mundo):
    assert cliente.get("/comunicados", headers=cabecera(mundo, "baja4")).status_code == 401


# ---- Quién publica ----------------------------------------------------------------------------


def test_presbitero_publica_para_todo_el_presbiterio(cliente, mundo):
    comunicado = publicar(cliente, mundo, "presbitero", iglesia_id=None)
    assert comunicado["iglesia_id"] is None
    assert comunicado["iglesia_nombre"] is None
    assert comunicado["vigente"] is True


def test_pastor_y_apoyo_publican_en_su_iglesia(cliente, mundo):
    for quien in ("pastor4", "apoyo4"):
        comunicado = publicar(
            cliente, mundo, quien, iglesia_id=mundo["cuarta"].id, titulo=f"Aviso de {quien}"
        )
        assert comunicado["iglesia_nombre"] == "4ta IAFCJ de Mérida"


@pytest.mark.parametrize("quien", ["pastor4", "apoyo4"])
def test_pastor_y_apoyo_no_publican_para_todo_el_presbiterio(cliente, mundo, quien):
    respuesta = cliente.post("/comunicados", json=cuerpo(), headers=cabecera(mundo, quien))
    assert respuesta.status_code == 403


def test_pastor_no_publica_en_otra_iglesia(cliente, mundo):
    respuesta = cliente.post(
        "/comunicados", json=cuerpo(mundo["sexta"].id), headers=cabecera(mundo, "pastor4")
    )
    assert respuesta.status_code == 403


@pytest.mark.parametrize("quien", ["tesorero4", "lider4"])
def test_otros_cargos_no_publican(cliente, mundo, quien):
    respuesta = cliente.post(
        "/comunicados", json=cuerpo(mundo["cuarta"].id), headers=cabecera(mundo, quien)
    )
    assert respuesta.status_code == 403


def test_quien_publica_queda_registrado(cliente, mundo, sesion):
    comunicado = publicar(cliente, mundo, "pastor4", iglesia_id=mundo["cuarta"].id)
    assert sesion.get(Comunicado, comunicado["id"]).creado_por == mundo["cuentas"]["pastor4"].id


# ---- Validación -------------------------------------------------------------------------------


def test_la_vigencia_no_puede_ser_anterior_a_hoy(cliente, mundo):
    respuesta = cliente.post(
        "/comunicados", json=cuerpo(vigente_hasta=AYER), headers=cabecera(mundo, "presbitero")
    )
    assert respuesta.status_code == 422


def test_se_puede_publicar_con_vigencia_hasta_hoy(cliente, mundo):
    assert publicar(cliente, mundo, "presbitero", vigente_hasta=HOY)["vigente"] is True


def test_iglesia_inexistente_da_422(cliente, mundo):
    respuesta = cliente.post(
        "/comunicados", json=cuerpo(999999), headers=cabecera(mundo, "presbitero")
    )
    assert respuesta.status_code == 422


@pytest.mark.parametrize(
    ("cambio", "campo"),
    [
        ({"titulo": ""}, "titulo"),
        ({"titulo": "x" * 151}, "titulo"),
        ({"contenido": "   "}, "contenido"),
        ({"contenido": "x" * 5001}, "contenido"),
        ({"vigente_hasta": "pronto"}, "vigente_hasta"),
    ],
)
def test_los_errores_de_formato_salen_en_espanol(cliente, mundo, cambio, campo):
    respuesta = cliente.post(
        "/comunicados", json=cuerpo() | cambio, headers=cabecera(mundo, "presbitero")
    )
    assert respuesta.status_code == 422
    assert [e["msg"] for e in respuesta.json()["detail"]] == [MENSAJES[campo]]


def test_un_dato_de_mas_da_422(cliente, mundo):
    respuesta = cliente.post(
        "/comunicados", json=cuerpo() | {"extra": 1}, headers=cabecera(mundo, "presbitero")
    )
    assert respuesta.status_code == 422


# ---- Solo los vigentes ------------------------------------------------------------------------


def test_solo_se_ven_los_vigentes(cliente, mundo, sesion):
    vigente = publicar(cliente, mundo, "presbitero")
    vencido(sesion, mundo)
    ids = [
        c["id"] for c in cliente.get("/comunicados", headers=cabecera(mundo, "presbitero")).json()
    ]
    assert ids == [vigente["id"]]


def test_cada_quien_ve_su_iglesia_y_el_presbiterio(cliente, mundo):
    general = publicar(cliente, mundo, "presbitero", titulo="General")
    de_cuarta = publicar(cliente, mundo, "pastor4", iglesia_id=mundo["cuarta"].id, titulo="Cuarta")
    de_sexta = publicar(cliente, mundo, "pastor6", iglesia_id=mundo["sexta"].id, titulo="Sexta")

    def ids(quien):
        return {c["id"] for c in cliente.get("/comunicados", headers=cabecera(mundo, quien)).json()}

    assert ids("presbitero") == {general["id"], de_cuarta["id"], de_sexta["id"]}
    assert ids("pastor4") == {general["id"], de_cuarta["id"]}
    assert ids("tesorero4") == {general["id"], de_cuarta["id"]}
    assert ids("lider4") == {general["id"], de_cuarta["id"]}
    assert ids("pastor6") == {general["id"], de_sexta["id"]}


def test_los_mas_recientes_van_primero(cliente, mundo):
    primero = publicar(cliente, mundo, "presbitero", titulo="Primero")
    segundo = publicar(cliente, mundo, "presbitero", titulo="Segundo")
    ids = [
        c["id"] for c in cliente.get("/comunicados", headers=cabecera(mundo, "presbitero")).json()
    ]
    assert ids == [segundo["id"], primero["id"]]


def test_detalle_de_otra_iglesia_no_se_revela(cliente, mundo):
    de_sexta = publicar(cliente, mundo, "pastor6", iglesia_id=mundo["sexta"].id)
    assert (
        cliente.get(
            f"/comunicados/{de_sexta['id']}", headers=cabecera(mundo, "pastor4")
        ).status_code
        == 404
    )
    assert (
        cliente.get(
            f"/comunicados/{de_sexta['id']}", headers=cabecera(mundo, "presbitero")
        ).status_code
        == 200
    )


def test_el_detalle_de_un_vencido_dice_que_ya_no_esta_vigente(cliente, mundo, sesion):
    viejo = vencido(sesion, mundo)
    respuesta = cliente.get(f"/comunicados/{viejo.id}", headers=cabecera(mundo, "pastor4"))
    assert respuesta.status_code == 200
    assert respuesta.json()["vigente"] is False


# ---- Editar -----------------------------------------------------------------------------------


def test_pastor_y_apoyo_editan_su_comunicado(cliente, mundo):
    comunicado = publicar(cliente, mundo, "pastor4", iglesia_id=mundo["cuarta"].id)
    nuevo = cuerpo(
        mundo["cuarta"].id, titulo="Aviso corregido", vigente_hasta=MANANA + timedelta(days=5)
    )
    respuesta = cliente.put(
        f"/comunicados/{comunicado['id']}", json=nuevo, headers=cabecera(mundo, "apoyo4")
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["titulo"] == "Aviso corregido"
    assert respuesta.json()["vigente_hasta"] == str(MANANA + timedelta(days=5))


def test_pastor_no_mueve_su_comunicado_a_otra_iglesia_ni_al_presbiterio(cliente, mundo):
    comunicado = publicar(cliente, mundo, "pastor4", iglesia_id=mundo["cuarta"].id)
    for destino in (mundo["sexta"].id, None):
        respuesta = cliente.put(
            f"/comunicados/{comunicado['id']}",
            json=cuerpo(destino),
            headers=cabecera(mundo, "pastor4"),
        )
        assert respuesta.status_code == 403


def test_presbitero_mueve_un_comunicado_a_otra_iglesia(cliente, mundo):
    comunicado = publicar(cliente, mundo, "pastor4", iglesia_id=mundo["cuarta"].id)
    respuesta = cliente.put(
        f"/comunicados/{comunicado['id']}",
        json=cuerpo(mundo["sexta"].id),
        headers=cabecera(mundo, "presbitero"),
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["iglesia_nombre"] == "6ta IAFCJ de Mérida"


def test_pastor_no_edita_uno_de_todo_el_presbiterio(cliente, mundo):
    general = publicar(cliente, mundo, "presbitero")
    respuesta = cliente.put(
        f"/comunicados/{general['id']}",
        json=cuerpo(mundo["cuarta"].id),
        headers=cabecera(mundo, "pastor4"),
    )
    assert respuesta.status_code == 403


def test_tesorero_no_edita(cliente, mundo):
    comunicado = publicar(cliente, mundo, "pastor4", iglesia_id=mundo["cuarta"].id)
    respuesta = cliente.put(
        f"/comunicados/{comunicado['id']}",
        json=cuerpo(mundo["cuarta"].id),
        headers=cabecera(mundo, "tesorero4"),
    )
    assert respuesta.status_code == 403


def test_editar_uno_ajeno_da_404(cliente, mundo):
    de_sexta = publicar(cliente, mundo, "pastor6", iglesia_id=mundo["sexta"].id)
    respuesta = cliente.put(
        f"/comunicados/{de_sexta['id']}",
        json=cuerpo(mundo["sexta"].id),
        headers=cabecera(mundo, "pastor4"),
    )
    assert respuesta.status_code == 404


def test_un_comunicado_vencido_no_se_edita(cliente, mundo, sesion):
    viejo = vencido(sesion, mundo, iglesia=mundo["cuarta"])
    respuesta = cliente.put(
        f"/comunicados/{viejo.id}",
        json=cuerpo(mundo["cuarta"].id),
        headers=cabecera(mundo, "pastor4"),
    )
    assert respuesta.status_code == 409


def test_editar_no_permite_dejar_la_vigencia_en_el_pasado(cliente, mundo):
    comunicado = publicar(cliente, mundo, "presbitero")
    respuesta = cliente.put(
        f"/comunicados/{comunicado['id']}",
        json=cuerpo(vigente_hasta=AYER),
        headers=cabecera(mundo, "presbitero"),
    )
    assert respuesta.status_code == 422


def test_editar_toma_el_candado_de_la_fila(cliente, mundo, sesion):
    comunicado = publicar(cliente, mundo, "pastor4", iglesia_id=mundo["cuarta"].id)
    sentencias = []

    @event.listens_for(sesion.get_bind(), "before_cursor_execute")
    def guardar(_conexion, _cursor, sentencia, *_resto):
        sentencias.append(sentencia)

    cliente.put(
        f"/comunicados/{comunicado['id']}",
        json=cuerpo(mundo["cuarta"].id, titulo="Otro"),
        headers=cabecera(mundo, "pastor4"),
    )
    assert [s for s in sentencias if "FOR UPDATE" in s and "comunicados" in s]


# ---- Duplicados -------------------------------------------------------------------------------


def test_un_doble_envio_no_publica_dos_veces(cliente, mundo):
    publicar(cliente, mundo, "pastor4", iglesia_id=mundo["cuarta"].id)
    repetido = cliente.post(
        "/comunicados", json=cuerpo(mundo["cuarta"].id), headers=cabecera(mundo, "pastor4")
    )
    assert repetido.status_code == 409
    # El mismo texto para otra iglesia o para todo el Presbiterio no es un duplicado.
    publicar(cliente, mundo, "presbitero")
    publicar(cliente, mundo, "presbitero", iglesia_id=mundo["sexta"].id)


def test_un_comunicado_vencido_no_cuenta_como_duplicado(cliente, mundo, sesion):
    vencido(sesion, mundo, titulo="Retiro de damas")
    sesion.get(Comunicado, sesion.query(Comunicado.id).scalar()).contenido = "Será el sábado."
    sesion.flush()
    publicar(cliente, mundo, "presbitero")
