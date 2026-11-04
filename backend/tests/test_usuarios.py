"""D19/D20: administración de cuentas y permisos con PostgreSQL temporal."""

import secrets
from typing import Annotated

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

# Reutiliza la infraestructura migrada del #7, sin alterar modelos ni migraciones.
from test_auth import motor_login as motor_login

from app.db import get_db
from app.main import crear_app
from app.modelos import CARGOS, Iglesia, Usuario
from app.seguridad.contrasenas import crear_hash, verificar_contrasena
from app.seguridad.permisos import requerir_cargos, requerir_permiso
from app.seguridad.tokens import crear_token


@pytest.fixture
def entorno(motor_login, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", secrets.token_urlsafe(32))
    with motor_login.connect() as conexion:
        transaccion = conexion.begin()
        with Session(bind=conexion, join_transaction_mode="create_savepoint") as sesion:
            iglesias = [Iglesia(nombre="Iglesia ficticia A"), Iglesia(nombre="Iglesia ficticia B")]
            sesion.add_all(iglesias)
            sesion.flush()
            hash_prueba = crear_hash(secrets.token_urlsafe(24))
            cuentas = {}
            for cargo in CARGOS:
                cuenta = Usuario(
                    nombre_usuario=f"cuenta.{cargo}",
                    nombre_completo=f"Persona ficticia {cargo}",
                    cargo=cargo,
                    iglesia_id=None if cargo == "presbitero" else iglesias[0].id,
                    activo=True,
                    contrasena_hash=hash_prueba,
                )
                cuentas[cargo] = cuenta
                sesion.add(cuenta)
            externo = Usuario(
                nombre_usuario="externo",
                nombre_completo="Otra persona ficticia",
                cargo="lider_celula",
                iglesia_id=iglesias[1].id,
                activo=True,
                contrasena_hash=hash_prueba,
            )
            sesion.add(externo)
            sesion.flush()
            # Fija los datos iniciales en la transacción externa de la prueba. Un 409
            # puede deshacer su propio SAVEPOINT sin quitar las cuentas iniciales.
            sesion.commit()
            app = crear_app()

            def sesion_prueba():
                yield sesion

            app.dependency_overrides[get_db] = sesion_prueba

            @app.get("/prueba/dinero/{iglesia_id}")
            def dinero(usuario: Annotated[Usuario, Depends(requerir_permiso(dinero=True))]):
                return {"ok": True}

            @app.get("/prueba/iglesia/{iglesia_id}")
            def iglesia(usuario: Annotated[Usuario, Depends(requerir_permiso())]):
                return {"ok": True}

            @app.get("/prueba/solo-pastor")
            def solo_pastor(usuario: Annotated[Usuario, Depends(requerir_cargos("pastor"))]):
                return {"ok": True}

            with TestClient(app) as cliente:
                try:
                    yield cliente, sesion, cuentas, iglesias, externo
                finally:
                    app.dependency_overrides.clear()
                    if transaccion.is_active:
                        transaccion.rollback()


def autorizacion(cuentas, cargo):
    return {"Authorization": f"Bearer {crear_token(str(cuentas[cargo].id))}"}


def datos_alta(iglesia_id, cargo="lider_celula"):
    return {
        "nombre_usuario": "cuenta.nueva",
        "nombre_completo": "Cuenta Nueva Ficticia",
        "cargo": cargo,
        "iglesia_id": iglesia_id,
        "contrasena": secrets.token_urlsafe(24),
    }


def cambios(cuenta, **valores):
    return {
        "nombre_completo": cuenta.nombre_completo,
        "cargo": cuenta.cargo,
        "iglesia_id": cuenta.iglesia_id,
        "activo": cuenta.activo,
        **valores,
    }


@pytest.mark.parametrize("cargo", CARGOS)
def test_yo_disponible_a_cuenta_activa_sin_hash(entorno, cargo):
    cliente, _, cuentas, _, _ = entorno
    respuesta = cliente.get("/usuarios/yo", headers=autorizacion(cuentas, cargo))
    assert respuesta.status_code == 200
    assert respuesta.json()["id"] == cuentas[cargo].id
    assert "contrasena_hash" not in respuesta.text
    assert "contrasena" not in respuesta.json()


@pytest.mark.parametrize(
    "cargo", [c for c in CARGOS if c not in {"presbitero", "pastor", "apoyo_pastor"}]
)
def test_cargos_sin_gestion_reciben_403_aunque_conozcan_url(entorno, cargo):
    cliente, _, cuentas, iglesias, _ = entorno
    headers = autorizacion(cuentas, cargo)
    assert cliente.get("/usuarios", headers=headers).status_code == 403
    assert cliente.get(f"/usuarios/{cuentas['pastor'].id}", headers=headers).status_code == 403
    assert (
        cliente.post("/usuarios", headers=headers, json=datos_alta(iglesias[0].id)).status_code
        == 403
    )
    respuesta = cliente.put(
        f"/usuarios/{cuentas[cargo].id}", headers=headers, json=cambios(cuentas[cargo])
    )
    assert respuesta.status_code == 403


@pytest.mark.parametrize("cargo", ["presbitero", "pastor", "apoyo_pastor"])
def test_alta_permitida_guarda_solo_hash(entorno, cargo, caplog):
    cliente, sesion, cuentas, iglesias, _ = entorno
    datos = datos_alta(iglesias[0].id)
    respuesta = cliente.post("/usuarios", headers=autorizacion(cuentas, cargo), json=datos)
    assert respuesta.status_code == 201
    cuenta = sesion.get(Usuario, respuesta.json()["id"])
    assert cuenta.contrasena_hash.startswith("$argon2id$")
    assert verificar_contrasena(datos["contrasena"], cuenta.contrasena_hash)
    assert datos["contrasena"] not in respuesta.text
    assert datos["contrasena"] not in caplog.text
    assert cuenta.contrasena_hash not in respuesta.text
    assert cuenta.contrasena_hash not in caplog.text


@pytest.mark.parametrize(
    "actor,cargo,estado",
    [
        ("apoyo_pastor", "tesorero", 403),
        ("apoyo_pastor", "pastor", 403),
        ("apoyo_pastor", "presbitero", 403),
        ("pastor", "tesorero", 201),
        ("pastor", "pastor", 403),
        ("presbitero", "pastor", 201),
        ("presbitero", "presbitero", 403),
    ],
)
def test_matriz_de_asignacion_al_crear(entorno, actor, cargo, estado):
    cliente, _, cuentas, iglesias, _ = entorno
    respuesta = cliente.post(
        "/usuarios", headers=autorizacion(cuentas, actor), json=datos_alta(iglesias[0].id, cargo)
    )
    assert respuesta.status_code == estado


@pytest.mark.parametrize("cargo", ["pastor", "apoyo_pastor"])
def test_no_crea_ni_edita_otra_iglesia(entorno, cargo):
    cliente, _, cuentas, iglesias, externo = entorno
    headers = autorizacion(cuentas, cargo)
    assert (
        cliente.post("/usuarios", headers=headers, json=datos_alta(iglesias[1].id)).status_code
        == 403
    )
    assert (
        cliente.put(f"/usuarios/{externo.id}", headers=headers, json=cambios(externo)).status_code
        == 403
    )
    cuenta = cuentas["lider_celula"]
    respuesta = cliente.put(
        f"/usuarios/{cuenta.id}", headers=headers, json=cambios(cuenta, iglesia_id=iglesias[1].id)
    )
    assert respuesta.status_code == 403


def test_presbitero_crea_en_otra_iglesia(entorno):
    cliente, _, cuentas, iglesias, _ = entorno
    respuesta = cliente.post(
        "/usuarios",
        headers=autorizacion(cuentas, "presbitero"),
        json=datos_alta(iglesias[1].id, "pastor"),
    )
    assert respuesta.status_code == 201


@pytest.mark.parametrize(
    "actor,cargo,estado",
    [
        ("apoyo_pastor", "tesorero", 403),
        ("apoyo_pastor", "pastor", 403),
        ("pastor", "pastor", 403),
        ("pastor", "tesorero", 200),
        ("presbitero", "pastor", 200),
        ("presbitero", "presbitero", 403),
    ],
)
def test_editar_no_evade_la_validacion_de_alta(entorno, actor, cargo, estado):
    cliente, sesion, cuentas, _, _ = entorno
    objetivo = cuentas["lider_celula"]
    respuesta = cliente.put(
        f"/usuarios/{objetivo.id}",
        headers=autorizacion(cuentas, actor),
        json=cambios(objetivo, cargo=cargo),
    )
    assert respuesta.status_code == estado
    sesion.refresh(objetivo)
    assert objetivo.cargo == (cargo if estado == 200 else "lider_celula")


@pytest.mark.parametrize("cargo,nuevo", [("apoyo_pastor", "lider_red"), ("pastor", "tesorero")])
def test_no_cambia_su_propio_cargo(entorno, cargo, nuevo):
    cliente, _, cuentas, _, _ = entorno
    cuenta = cuentas[cargo]
    respuesta = cliente.put(
        f"/usuarios/{cuenta.id}",
        headers=autorizacion(cuentas, cargo),
        json=cambios(cuenta, cargo=nuevo),
    )
    assert respuesta.status_code == 403


@pytest.mark.parametrize("cargo", ["pastor", "apoyo_pastor"])
def test_puede_editar_su_nombre_sin_cambiar_cargo(entorno, cargo):
    cliente, _, cuentas, _, _ = entorno
    cuenta = cuentas[cargo]
    respuesta = cliente.put(
        f"/usuarios/{cuenta.id}",
        headers=autorizacion(cuentas, cargo),
        json=cambios(cuenta, nombre_completo="Nuevo nombre ficticio"),
    )
    assert respuesta.status_code == 200


@pytest.mark.parametrize("cargo", ["pastor", "tesorero"])
def test_apoyo_no_modifica_cuenta_con_dinero(entorno, cargo):
    cliente, _, cuentas, _, _ = entorno
    objetivo = cuentas[cargo]
    respuesta = cliente.put(
        f"/usuarios/{objetivo.id}",
        headers=autorizacion(cuentas, "apoyo_pastor"),
        json=cambios(objetivo, activo=False),
    )
    assert respuesta.status_code == 403


@pytest.mark.parametrize("cargo", ["pastor", "apoyo_pastor", "presbitero"])
def test_lista_filtra_en_servidor_y_no_incluye_hash(entorno, cargo):
    cliente, _, cuentas, iglesias, externo = entorno
    respuesta = cliente.get("/usuarios", headers=autorizacion(cuentas, cargo))
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert "contrasena_hash" not in respuesta.text
    assert (externo.id in {u["id"] for u in datos}) == (cargo == "presbitero")
    if cargo != "presbitero":
        assert all(u["iglesia_id"] == iglesias[0].id for u in datos)
    assert all("iglesia_nombre" in u for u in datos)


def test_duplicado_sin_distinguir_mayusculas_da_409(entorno):
    cliente, sesion, cuentas, iglesias, _ = entorno
    datos = datos_alta(iglesias[0].id)
    datos["nombre_usuario"] = cuentas["tesorero"].nombre_usuario.upper()
    respuesta = cliente.post("/usuarios", headers=autorizacion(cuentas, "pastor"), json=datos)
    assert respuesta.status_code == 409
    # La sesión sigue siendo utilizable tras deshacer el INSERT rechazado.
    assert sesion.scalar(select(Usuario).where(Usuario.id == cuentas["tesorero"].id)) is not None


@pytest.mark.parametrize("cambio", ["desactivar", "borrar"])
def test_cuenta_ya_no_valida_pierde_acceso_con_token_existente(entorno, cambio):
    cliente, sesion, cuentas, _, _ = entorno
    cuenta = cuentas["lider_celula"]
    headers = autorizacion(cuentas, "lider_celula")
    if cambio == "desactivar":
        cuenta.activo = False
    else:
        sesion.delete(cuenta)
    sesion.flush()
    assert cliente.get("/usuarios/yo", headers=headers).status_code == 401


def test_cargo_se_lee_de_la_base_en_cada_peticion(entorno):
    cliente, sesion, cuentas, _, _ = entorno
    headers = autorizacion(cuentas, "pastor")
    assert cliente.get("/prueba/solo-pastor", headers=headers).status_code == 200
    cuentas["pastor"].cargo = "lider_celula"
    sesion.flush()
    assert cliente.get("/prueba/solo-pastor", headers=headers).status_code == 403


@pytest.mark.parametrize("cargo", CARGOS)
def test_dinero_solo_cargos_permitidos_en_su_iglesia(entorno, cargo):
    cliente, _, cuentas, iglesias, _ = entorno
    headers = autorizacion(cuentas, cargo)
    for indice, iglesia in enumerate(iglesias):
        respuesta = cliente.get(f"/prueba/dinero/{iglesia.id}", headers=headers)
        permitido = cargo == "presbitero" or (cargo in {"pastor", "tesorero"} and indice == 0)
        assert respuesta.status_code == (200 if permitido else 403)


def test_lider_no_recibe_acceso_general_mientras_area_esta_pendiente(entorno):
    cliente, _, cuentas, iglesias, _ = entorno
    respuesta = cliente.get(
        f"/prueba/iglesia/{iglesias[0].id}", headers=autorizacion(cuentas, "lider_celula")
    )
    assert respuesta.status_code == 403


def test_peticion_sin_sesion_recibe_401(entorno):
    cliente, _, _, _, _ = entorno
    assert cliente.get("/usuarios").status_code == 401


def test_validacion_de_alta_no_refleja_contrasena(entorno):
    cliente, _, cuentas, iglesias, _ = entorno
    datos = datos_alta(iglesias[0].id, "cargo inventado")
    respuesta = cliente.post("/usuarios", headers=autorizacion(cuentas, "pastor"), json=datos)
    assert respuesta.status_code == 422
    assert datos["contrasena"] not in respuesta.text


def test_no_se_admiten_campos_ocultos_para_escalar_permisos(entorno):
    cliente, _, cuentas, iglesias, _ = entorno
    datos = {**datos_alta(iglesias[0].id), "activo": True, "contrasena_hash": "inventado"}
    assert (
        cliente.post(
            "/usuarios", headers=autorizacion(cuentas, "apoyo_pastor"), json=datos
        ).status_code
        == 422
    )


def test_presbitero_puede_cambiar_su_propio_cargo_segun_d20(entorno):
    cliente, _, cuentas, iglesias, _ = entorno
    cuenta = cuentas["presbitero"]
    respuesta = cliente.put(
        f"/usuarios/{cuenta.id}",
        headers=autorizacion(cuentas, "presbitero"),
        json=cambios(cuenta, cargo="pastor", iglesia_id=iglesias[0].id),
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["cargo"] == "pastor"


def test_desactivar_por_api_revoca_la_cuenta_sin_borrarla(entorno):
    cliente, sesion, cuentas, _, _ = entorno
    cuenta = cuentas["lider_celula"]
    headers_lider = autorizacion(cuentas, "lider_celula")
    respuesta = cliente.put(
        f"/usuarios/{cuenta.id}",
        headers=autorizacion(cuentas, "pastor"),
        json=cambios(cuenta, activo=False),
    )
    assert respuesta.status_code == 200
    assert sesion.get(Usuario, cuenta.id) is not None
    assert cliente.get("/usuarios/yo", headers=headers_lider).status_code == 401
