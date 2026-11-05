"""Hojas y marcas de asistencia (#23), según AGENTS.md §9 y las decisiones D16 y D21.

- El líder de célula ve y marca SU célula (la que dirige su ficha de miembro): quién asistió.
- El ujier ve a los miembros de su iglesia que no tienen célula y marca quién faltó.
- Nadie más tiene hojas. Una persona no se marca dos veces el mismo día y culto: cada marca
  reemplaza a la anterior (hay una sola fila por persona, fecha y culto).
"""

from dataclasses import dataclass
from datetime import date
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Asistencia, Grupo, GrupoMiembro, Miembro, Usuario
from app.modulos.asistencia.schemas import GuardarHoja, HojaRespuesta, PersonaHoja
from app.seguridad.tokens import obtener_usuario_id


# shortcut: copia de `denegar` y `obtener_usuario_actual` del PR #56 (app/seguridad/permisos.py)
# para que este módulo no dependa de él. Cuando el #56 esté en main, importar de allí y borrar
# estas dos funciones.
def denegar() -> None:
    raise HTTPException(status_code=403, detail="No tienes permiso para realizar esta acción.")


def obtener_usuario_actual(
    sujeto: Annotated[str, Depends(obtener_usuario_id)],
    sesion: Annotated[Session, Depends(get_db)],
) -> Usuario:
    try:
        identificador = int(sujeto)
    except ValueError:
        identificador = 0
    usuario = sesion.get(Usuario, identificador) if identificador > 0 else None
    if usuario is None or not usuario.activo:
        raise HTTPException(
            status_code=401,
            detail="Sesión no válida o vencida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


@dataclass
class Hoja:
    id: str
    modo: str
    titulo: str
    personas: list[Miembro]


def hojas_del_usuario(sesion: Session, actor: Usuario) -> list[Hoja]:
    if actor.cargo == "lider_celula" and actor.miembro_id is not None:
        celulas = sesion.scalars(
            select(Grupo)
            .where(
                Grupo.tipo == "celula",
                Grupo.activo.is_(True),
                Grupo.lider_miembro_id == actor.miembro_id,
                Grupo.iglesia_id == actor.iglesia_id,
            )
            .order_by(Grupo.nombre, Grupo.id)
        ).all()
        hojas = []
        for celula in celulas:
            integrantes = sesion.scalars(
                select(Miembro)
                .join(GrupoMiembro, GrupoMiembro.miembro_id == Miembro.id)
                .where(GrupoMiembro.grupo_id == celula.id)
                .order_by(Miembro.nombre, Miembro.id)
            ).all()
            hojas.append(
                Hoja(f"celula:{celula.id}", "asistencias", celula.nombre, list(integrantes))
            )
        return hojas
    if actor.cargo == "ujier":
        con_celula = select(GrupoMiembro.miembro_id).where(GrupoMiembro.tipo_grupo == "celula")
        sin_celula = sesion.scalars(
            select(Miembro)
            .where(
                Miembro.iglesia_id == actor.iglesia_id,
                Miembro.estado != "inactivo",
                Miembro.id.not_in(con_celula),
            )
            .order_by(Miembro.nombre, Miembro.id)
        ).all()
        return [Hoja(f"sin_celula:{actor.iglesia_id}", "faltas", "Sin célula", list(sin_celula))]
    return []


def _registros(sesion: Session, hoja: Hoja, fecha: date, servicio: str) -> dict[int, Asistencia]:
    ids = [m.id for m in hoja.personas]
    if not ids:
        return {}
    filas = sesion.scalars(
        select(Asistencia).where(
            Asistencia.fecha == fecha,
            Asistencia.tipo_servicio == servicio,
            Asistencia.miembro_id.in_(ids),
        )
    )
    return {a.miembro_id: a for a in filas}


def _respuesta(hoja: Hoja, registros: dict[int, Asistencia]) -> HojaRespuesta:
    asistencias = hoja.modo == "asistencias"
    return HojaRespuesta(
        hoja=hoja.id,
        modo=hoja.modo,
        titulo=hoja.titulo,
        guardada=bool(registros),
        personas=[
            PersonaHoja(
                miembro_id=m.id,
                nombre=m.nombre,
                # En una célula se marca a quien asistió; en "sin célula", a quien faltó.
                marcado=m.id in registros and registros[m.id].presente == asistencias,
            )
            for m in hoja.personas
        ],
    )


def obtener_hojas(
    sesion: Session, actor: Usuario, fecha: date, servicio: str
) -> list[HojaRespuesta]:
    return [
        _respuesta(hoja, _registros(sesion, hoja, fecha, servicio))
        for hoja in hojas_del_usuario(sesion, actor)
    ]


def guardar_hoja(sesion: Session, actor: Usuario, datos: GuardarHoja) -> HojaRespuesta:
    hoja = next((h for h in hojas_del_usuario(sesion, actor) if h.id == datos.hoja), None)
    if hoja is None:
        denegar()
    marcados = set(datos.marcados)
    if not marcados <= {m.id for m in hoja.personas}:
        raise HTTPException(status_code=422, detail="Hay personas que no están en tu lista.")
    registros = _registros(sesion, hoja, datos.fecha, datos.servicio)
    asistencias = hoja.modo == "asistencias"
    for persona in hoja.personas:
        marcada = persona.id in marcados
        # En una célula, marcar es "asistió"; en "sin célula", marcar es "faltó".
        presente = marcada if asistencias else not marcada
        existente = registros.get(persona.id)
        if existente is None:
            sesion.add(
                Asistencia(
                    miembro_id=persona.id,
                    fecha=datos.fecha,
                    tipo_servicio=datos.servicio,
                    presente=presente,
                    registrado_por=actor.id,
                )
            )
        else:
            existente.presente = presente
            existente.registrado_por = actor.id
    try:
        sesion.commit()
    except IntegrityError:
        sesion.rollback()
        raise HTTPException(
            status_code=409,
            detail="Alguien guardó esta lista al mismo tiempo. Ábrela de nuevo.",
        ) from None
    return _respuesta(hoja, _registros(sesion, hoja, datos.fecha, datos.servicio))
