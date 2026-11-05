"""Alta, consulta y edición de cuentas con la misma política D19/D20."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modelos import Iglesia, Miembro, Usuario
from app.modulos.usuarios.schemas import (
    UsuarioCambios,
    UsuarioNuevo,
    UsuarioRespuesta,
    UsuarioResumen,
)
from app.seguridad.contrasenas import crear_hash
from app.seguridad.permisos import denegar

GESTORES = {"presbitero", "pastor", "apoyo_pastor"}
CON_DINERO = {"presbitero", "pastor", "tesorero"}


def validar_asignacion(
    actor: Usuario, cargo: str, iglesia_id: int | None, objetivo: Usuario | None = None
) -> None:
    if actor.cargo not in GESTORES:
        denegar()
    if actor.cargo != "presbitero":
        if iglesia_id != actor.iglesia_id:
            denegar()
        if objetivo is not None:
            if objetivo.iglesia_id != actor.iglesia_id:
                denegar()
            if objetivo.id == actor.id:
                if cargo != objetivo.cargo:
                    denegar()
            elif objetivo.cargo == "presbitero" or objetivo.cargo == "pastor":
                denegar()
            elif actor.cargo == "apoyo_pastor" and objetivo.cargo in CON_DINERO:
                denegar()
        if cargo == "presbitero":
            denegar()
        # Conservar el cargo propio al editar el perfil no equivale a asignarlo.
        propio_sin_cambio = (
            objetivo is not None and objetivo.id == actor.id and cargo == actor.cargo
        )
        if cargo == "pastor" and not propio_sin_cambio:
            denegar()
        if actor.cargo == "apoyo_pastor" and cargo in CON_DINERO:
            denegar()
    if cargo == "presbitero" and (objetivo is None or objetivo.cargo != "presbitero"):
        denegar()


def validar_iglesia(sesion: Session, cargo: str, iglesia_id: int | None) -> None:
    if iglesia_id is None:
        if cargo != "presbitero":
            raise HTTPException(status_code=422, detail="Este cargo requiere una iglesia.")
    elif sesion.get(Iglesia, iglesia_id) is None:
        raise HTTPException(status_code=422, detail="La iglesia indicada no existe.")


def validar_miembro(
    sesion: Session,
    actor: Usuario,
    iglesia_id: int | None,
    miembro_id: int | None,
    objetivo: Usuario | None = None,
) -> None:
    if miembro_id is None:
        return
    miembro = sesion.get(Miembro, miembro_id)
    if miembro is None:
        raise HTTPException(status_code=422, detail="La ficha de miembro indicada no existe.")
    if actor.cargo != "presbitero" and miembro.iglesia_id != actor.iglesia_id:
        denegar()
    if iglesia_id is not None and miembro.iglesia_id != iglesia_id:
        raise HTTPException(
            status_code=422, detail="La ficha debe pertenecer a la iglesia de la cuenta."
        )
    consulta = select(Usuario.id).where(Usuario.miembro_id == miembro_id)
    if objetivo is not None:
        consulta = consulta.where(Usuario.id != objetivo.id)
    if sesion.scalar(consulta) is not None:
        raise HTTPException(
            status_code=409, detail="La ficha de miembro ya está vinculada a una cuenta."
        )


def obtener_cuenta(sesion: Session, actor: Usuario, identificador: int) -> Usuario:
    if actor.cargo not in GESTORES:
        denegar()
    cuenta = sesion.get(Usuario, identificador)
    if cuenta is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if actor.cargo != "presbitero" and cuenta.iglesia_id != actor.iglesia_id:
        denegar()
    return cuenta


def listar_cuentas(sesion: Session, actor: Usuario) -> list[UsuarioResumen]:
    if actor.cargo not in GESTORES:
        denegar()
    consulta = select(Usuario, Iglesia.nombre).outerjoin(Iglesia, Usuario.iglesia_id == Iglesia.id)
    if actor.cargo != "presbitero":
        consulta = consulta.where(Usuario.iglesia_id == actor.iglesia_id)
    filas = sesion.execute(consulta.order_by(Usuario.nombre_usuario)).all()
    return [
        UsuarioResumen(
            **UsuarioRespuesta.model_validate(cuenta).model_dump(), iglesia_nombre=nombre
        )
        for cuenta, nombre in filas
    ]


def guardar(sesion: Session, cuenta: Usuario) -> Usuario:
    try:
        sesion.commit()
    except IntegrityError as error:
        restriccion = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        sesion.rollback()
        if restriccion == "uq_usuarios_miembro_id":
            raise HTTPException(
                status_code=409, detail="La ficha de miembro ya está vinculada a una cuenta."
            ) from None
        raise HTTPException(status_code=409, detail="Ese nombre de usuario ya existe.") from None
    sesion.refresh(cuenta)
    return cuenta


def crear_cuenta(sesion: Session, actor: Usuario, datos: UsuarioNuevo) -> Usuario:
    validar_asignacion(actor, datos.cargo, datos.iglesia_id)
    validar_iglesia(sesion, datos.cargo, datos.iglesia_id)
    validar_miembro(sesion, actor, datos.iglesia_id, datos.miembro_id)
    cuenta = Usuario(
        nombre_usuario=datos.nombre_usuario,
        nombre_completo=datos.nombre_completo,
        contrasena_hash=crear_hash(datos.contrasena.get_secret_value()),
        cargo=datos.cargo,
        iglesia_id=datos.iglesia_id,
        miembro_id=datos.miembro_id,
        activo=True,
    )
    sesion.add(cuenta)
    return guardar(sesion, cuenta)


def actualizar_cuenta(
    sesion: Session, actor: Usuario, identificador: int, datos: UsuarioCambios
) -> Usuario:
    cuenta = obtener_cuenta(sesion, actor, identificador)
    validar_asignacion(actor, datos.cargo, datos.iglesia_id, cuenta)
    validar_iglesia(sesion, datos.cargo, datos.iglesia_id)
    miembro_id = datos.miembro_id if "miembro_id" in datos.model_fields_set else cuenta.miembro_id
    validar_miembro(sesion, actor, datos.iglesia_id, miembro_id, cuenta)
    cuenta.nombre_completo = datos.nombre_completo
    cuenta.cargo = datos.cargo
    cuenta.iglesia_id = datos.iglesia_id
    cuenta.activo = datos.activo
    cuenta.miembro_id = miembro_id
    return guardar(sesion, cuenta)
