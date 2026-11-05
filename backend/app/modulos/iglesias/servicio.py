"""Alta y edición atómicas; los identificadores hijos se validan en el servidor."""

from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modelos import Horario, Iglesia, RedSocial, Sede, Usuario
from app.modulos.iglesias.schemas import IglesiaEntrada
from app.seguridad.permisos import denegar

CAMPOS = ("nombre", "foto_url", "pastor", "telefono_pastor", "telefono_iglesia")


def listar_iglesias(sesion: Session, actor: Usuario):
    consulta = (
        select(
            Iglesia.id,
            Iglesia.nombre,
            Iglesia.foto_url,
            Iglesia.pastor,
            func.count(Sede.id).label("total_sedes"),
        )
        .outerjoin(Sede, Sede.iglesia_id == Iglesia.id)
        .group_by(Iglesia.id)
        .order_by(Iglesia.nombre, Iglesia.id)
    )
    if actor.cargo != "presbitero":
        consulta = consulta.where(Iglesia.id == actor.iglesia_id)
    return sesion.execute(consulta).mappings().all()


def cargar_iglesia(sesion: Session, actor: Usuario, identificador: int) -> Iglesia:
    if actor.cargo != "presbitero" and actor.iglesia_id != identificador:
        denegar()
    iglesia = sesion.get(Iglesia, identificador)
    if iglesia is None:
        raise HTTPException(status_code=404, detail="Iglesia no encontrada.")
    return iglesia


def hijos(sesion: Session, modelo, identificador: int):
    return list(
        sesion.scalars(select(modelo).where(modelo.iglesia_id == identificador).order_by(modelo.id))
    )


def respuesta(sesion: Session, iglesia: Iglesia):
    return {
        "id": iglesia.id,
        **{campo: getattr(iglesia, campo) for campo in CAMPOS},
        "sedes": hijos(sesion, Sede, iglesia.id),
        "redes": hijos(sesion, RedSocial, iglesia.id),
    }


def obtener_iglesia(sesion: Session, actor: Usuario, identificador: int):
    return respuesta(sesion, cargar_iglesia(sesion, actor, identificador))


def guardar(sesion: Session):
    try:
        sesion.commit()
    except IntegrityError as error:
        sesion.rollback()
        raise HTTPException(
            status_code=409,
            detail="El nombre ya existe o hay datos relacionados que impiden el cambio.",
        ) from error


def crear_iglesia(sesion: Session, actor: Usuario, datos: IglesiaEntrada):
    if actor.cargo != "presbitero":
        denegar()
    if any(h.id is not None for h in [*datos.sedes, *datos.redes]):
        raise HTTPException(status_code=422, detail="Las sedes y redes nuevas no llevan id.")
    iglesia = Iglesia(**datos.model_dump(include=set(CAMPOS)))
    try:
        sesion.add(iglesia)
        sesion.flush()
        for modelo, entradas in ((Sede, datos.sedes), (RedSocial, datos.redes)):
            sesion.add_all(
                [modelo(iglesia_id=iglesia.id, **e.model_dump(exclude={"id"})) for e in entradas]
            )
        guardar(sesion)
    except IntegrityError as error:
        sesion.rollback()
        raise HTTPException(
            status_code=409, detail="Ya existe una iglesia con ese nombre."
        ) from error
    return respuesta(sesion, iglesia)


def actualizar_iglesia(
    sesion: Session,
    actor: Usuario,
    identificador: int,
    datos: IglesiaEntrada,
):
    if actor.cargo not in {"presbitero", "pastor", "apoyo_pastor"}:
        denegar()
    iglesia = cargar_iglesia(sesion, actor, identificador)
    # Bloquea el agregado mientras se validan y reemplazan sus listas.
    sesion.refresh(iglesia, with_for_update=True)
    existentes = {
        Sede: {s.id: s for s in hijos(sesion, Sede, iglesia.id)},
        RedSocial: {r.id: r for r in hijos(sesion, RedSocial, iglesia.id)},
    }
    for modelo, entradas in ((Sede, datos.sedes), (RedSocial, datos.redes)):
        if any(e.id is not None and e.id not in existentes[modelo] for e in entradas):
            denegar()
    conservadas = {s.id for s in datos.sedes if s.id is not None}
    retiradas = set(existentes[Sede]) - conservadas
    if retiradas and sesion.scalar(
        select(Horario.id).where(Horario.sede_id.in_(retiradas)).limit(1)
    ):
        raise HTTPException(
            status_code=409,
            detail="Esta sede tiene horarios; elimínalos primero.",
        )
    try:
        # Nombres provisionales dentro de la transacción permiten intercambiar nombres
        # entre sedes sin violar su restricción UNIQUE durante los UPDATE individuales.
        for sede in existentes[Sede].values():
            sede.nombre = f"temporal-{uuid4().hex}"
        sesion.flush()
        for modelo, entradas in ((Sede, datos.sedes), (RedSocial, datos.redes)):
            ids = {e.id for e in entradas if e.id is not None}
            for id_hijo, objeto in existentes[modelo].items():
                if id_hijo not in ids:
                    sesion.delete(objeto)
            for entrada in entradas:
                objeto = existentes[modelo].get(entrada.id)
                if objeto is None:
                    objeto = modelo(iglesia_id=iglesia.id)
                    sesion.add(objeto)
                for campo, valor in entrada.model_dump(exclude={"id"}).items():
                    setattr(objeto, campo, valor)
        for campo in CAMPOS:
            setattr(iglesia, campo, getattr(datos, campo))
        guardar(sesion)
    except IntegrityError as error:
        sesion.rollback()
        raise HTTPException(status_code=409, detail="No se puede guardar este cambio.") from error
    return respuesta(sesion, iglesia)
