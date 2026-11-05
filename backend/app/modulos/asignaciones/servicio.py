"""Gestores agregan; el líder solo quita en sus grupos (confirmado para #22)."""

from fastapi import HTTPException
from sqlalchemy import false, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modelos import Grupo, GrupoMiembro, Iglesia, Miembro, Usuario
from app.seguridad.permisos import denegar, validar_alcance

GESTORES = {"presbitero", "pastor", "apoyo_pastor"}


def listar_grupos(sesion: Session, actor: Usuario):
    if actor.cargo == "tesorero":
        denegar()
    consulta = (
        select(
            Grupo.id,
            Grupo.nombre,
            Grupo.tipo,
            Grupo.iglesia_id,
            Grupo.activo,
            Iglesia.nombre.label("iglesia_nombre"),
        )
        .join(Iglesia, Iglesia.id == Grupo.iglesia_id)
        .order_by(Iglesia.nombre, Grupo.nombre, Grupo.id)
    )
    if actor.cargo != "presbitero":
        consulta = consulta.where(Grupo.iglesia_id == actor.iglesia_id)
    if actor.cargo not in GESTORES:
        consulta = consulta.where(
            Grupo.activo.is_(True),
            Grupo.lider_miembro_id == actor.miembro_id if actor.miembro_id is not None else false(),
        )
    return sesion.execute(consulta).mappings().all()


def obtener_grupo(sesion: Session, actor: Usuario, identificador: int, *, bloquear=False) -> Grupo:
    if actor.cargo == "tesorero":
        denegar()
    consulta = select(Grupo).where(Grupo.id == identificador)
    if bloquear:
        consulta = consulta.with_for_update()
    grupo = sesion.scalar(consulta)
    if grupo is None:
        raise HTTPException(status_code=404, detail="Grupo no encontrado.")
    validar_alcance(sesion, actor, grupo.iglesia_id, area_id=grupo.id)
    return grupo


def integrantes(sesion: Session, actor: Usuario, grupo_id: int):
    grupo = obtener_grupo(sesion, actor, grupo_id)
    return list(
        sesion.scalars(
            select(Miembro)
            .join(GrupoMiembro, GrupoMiembro.miembro_id == Miembro.id)
            .where(GrupoMiembro.grupo_id == grupo.id, Miembro.iglesia_id == grupo.iglesia_id)
            .order_by(Miembro.nombre, Miembro.id)
        )
    )


def candidatos(sesion: Session, actor: Usuario, grupo_id: int):
    if actor.cargo not in GESTORES:
        denegar()
    grupo = obtener_grupo(sesion, actor, grupo_id)
    if not grupo.activo:
        raise HTTPException(
            status_code=422, detail="El grupo está inactivo; solo puedes quitar integrantes."
        )
    asignados = select(GrupoMiembro.miembro_id).where(GrupoMiembro.grupo_id == grupo.id)
    consulta = select(Miembro).where(
        Miembro.iglesia_id == grupo.iglesia_id, Miembro.id.not_in(asignados)
    )
    if grupo.tipo == "celula":
        con_celula = select(GrupoMiembro.miembro_id).where(GrupoMiembro.tipo_grupo == "celula")
        consulta = consulta.where(Miembro.id.not_in(con_celula))
    return list(sesion.scalars(consulta.order_by(Miembro.nombre, Miembro.id)))


def guardar(sesion: Session):
    try:
        sesion.commit()
    except IntegrityError as error:
        sesion.rollback()
        raise HTTPException(
            status_code=409,
            detail="La asignación cambió o el miembro ya tiene célula. Recarga la página.",
        ) from error


def asignar(sesion: Session, actor: Usuario, grupo_id: int, miembro_id: int):
    if actor.cargo not in GESTORES:
        denegar()
    grupo = obtener_grupo(sesion, actor, grupo_id, bloquear=True)
    if not grupo.activo:
        raise HTTPException(
            status_code=422, detail="No se pueden agregar integrantes a un grupo inactivo."
        )
    miembro = sesion.scalar(select(Miembro).where(Miembro.id == miembro_id).with_for_update())
    if miembro is None or miembro.iglesia_id != grupo.iglesia_id:
        raise HTTPException(
            status_code=422, detail="El miembro no existe o no pertenece a la iglesia del grupo."
        )
    if sesion.get(GrupoMiembro, (grupo.id, miembro.id)) is not None:
        raise HTTPException(status_code=409, detail="El miembro ya está asignado a este grupo.")
    if (
        grupo.tipo == "celula"
        and sesion.scalar(
            select(GrupoMiembro.grupo_id).where(
                GrupoMiembro.miembro_id == miembro.id,
                GrupoMiembro.tipo_grupo == "celula",
            )
        )
        is not None
    ):
        raise HTTPException(
            status_code=409,
            detail="El miembro ya pertenece a una célula. Quita primero la asignación anterior.",
        )
    sesion.add(GrupoMiembro(grupo_id=grupo.id, miembro_id=miembro.id, tipo_grupo=grupo.tipo))
    guardar(sesion)
    return {"grupo_id": grupo.id, "miembro_id": miembro.id}


def quitar(sesion: Session, actor: Usuario, grupo_id: int, miembro_id: int):
    grupo = obtener_grupo(sesion, actor, grupo_id, bloquear=True)
    asignacion = sesion.get(GrupoMiembro, (grupo.id, miembro_id))
    if asignacion is None:
        raise HTTPException(status_code=404, detail="La asignación no existe.")
    sesion.delete(asignacion)
    guardar(sesion)
