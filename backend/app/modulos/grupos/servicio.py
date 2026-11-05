"""Alcance y operaciones de grupos (#20), según AGENTS.md §9 y las decisiones D9, D20 y D21.

Quién ve qué grupos:
- Presbítero: todos. Pastor y apoyo del pastor: los de su iglesia.
- Tesorero: ninguno (su área no incluye grupos; igual que `permisos.validar_alcance`).
- Cualquier otro cargo: solo los grupos que dirige su ficha de miembro (D21).

Quién crea y edita: presbítero, pastor y apoyo, dentro de su iglesia (D20, regla 5).
Un líder "solo administra su grupo" (criterio del #20): puede cambiar el nombre y el asistente de
SU grupo, pero no su líder, su tipo ni su iglesia.
"""

from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy import Select, false, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Grupo, GrupoMiembro, Iglesia, Miembro, Usuario
from app.modulos.grupos.schemas import GrupoEntrada, GrupoRespuesta, GrupoResumen
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


GESTORES = {"presbitero", "pastor", "apoyo_pastor"}


def no_encontrado() -> HTTPException:
    return HTTPException(status_code=404, detail="Este grupo no existe o no está en tu alcance.")


def _invalido(detalle: str) -> HTTPException:
    return HTTPException(status_code=422, detail=detalle)


def _visibles(actor: Usuario) -> Select:
    if actor.cargo == "tesorero":
        denegar()
    consulta = select(Grupo).where(Grupo.activo.is_(True))
    if actor.cargo == "presbitero":
        return consulta
    if actor.cargo in GESTORES:
        return consulta.where(Grupo.iglesia_id == actor.iglesia_id)
    if actor.miembro_id is None:
        return consulta.where(false())
    return consulta.where(
        Grupo.lider_miembro_id == actor.miembro_id, Grupo.iglesia_id == actor.iglesia_id
    )


def _respuesta(grupo: Grupo) -> GrupoRespuesta:
    return GrupoRespuesta(
        id=grupo.id,
        nombre=grupo.nombre,
        tipo=grupo.tipo,
        iglesia_id=grupo.iglesia_id,
        lider_id=grupo.lider_miembro_id,
        asistente_id=grupo.asistente_miembro_id,
    )


def listar_grupos(sesion: Session, actor: Usuario, tipo: str | None = None) -> list[GrupoResumen]:
    consulta = _visibles(actor)
    if tipo is not None:
        consulta = consulta.where(Grupo.tipo == tipo)
    grupos = sesion.scalars(consulta).all()
    ids_miembros = {g.lider_miembro_id for g in grupos} | {
        g.asistente_miembro_id for g in grupos if g.asistente_miembro_id is not None
    }
    nombres_miembros = {
        m.id: m.nombre for m in sesion.scalars(select(Miembro).where(Miembro.id.in_(ids_miembros)))
    }
    nombres_iglesias = {i.id: i.nombre for i in sesion.scalars(select(Iglesia))}
    resultado = [
        GrupoResumen(
            id=g.id,
            nombre=g.nombre,
            tipo=g.tipo,
            iglesia_id=g.iglesia_id,
            iglesia_nombre=nombres_iglesias[g.iglesia_id],
            lider_nombre=nombres_miembros.get(g.lider_miembro_id),
            asistente_nombre=nombres_miembros.get(g.asistente_miembro_id),
        )
        for g in grupos
    ]
    return sorted(resultado, key=lambda g: (g.nombre.casefold(), g.id))


def _grupo_visible(sesion: Session, actor: Usuario, identificador: int) -> Grupo:
    grupo = sesion.scalar(_visibles(actor).where(Grupo.id == identificador))
    if grupo is None:
        raise no_encontrado()
    return grupo


def obtener_grupo(sesion: Session, actor: Usuario, identificador: int) -> GrupoRespuesta:
    return _respuesta(_grupo_visible(sesion, actor, identificador))


def _exigir_gestion(sesion: Session, actor: Usuario, iglesia_id: int) -> None:
    if actor.cargo not in GESTORES:
        denegar()
    if actor.cargo != "presbitero" and iglesia_id != actor.iglesia_id:
        denegar()
    if sesion.get(Iglesia, iglesia_id) is None:
        raise _invalido("La iglesia indicada no existe.")


def _validar_personas(sesion: Session, datos: GrupoEntrada) -> None:
    lider = sesion.get(Miembro, datos.lider_id)
    if lider is None:
        raise _invalido("El líder indicado no existe.")
    if lider.iglesia_id != datos.iglesia_id:
        raise _invalido("El líder debe ser miembro de la iglesia del grupo.")
    if datos.asistente_id is None:
        return
    if datos.asistente_id == datos.lider_id:
        raise _invalido("El asistente debe ser otra persona.")
    asistente = sesion.get(Miembro, datos.asistente_id)
    if asistente is None:
        raise _invalido("El asistente indicado no existe.")
    if asistente.iglesia_id != datos.iglesia_id:
        raise _invalido("El asistente debe ser miembro de la iglesia del grupo.")


def _validar_nombre_unico(sesion: Session, datos: GrupoEntrada, propio: int | None) -> None:
    consulta = select(Grupo.id).where(
        Grupo.iglesia_id == datos.iglesia_id,
        Grupo.tipo == datos.tipo,
        Grupo.nombre == datos.nombre,
    )
    if propio is not None:
        consulta = consulta.where(Grupo.id != propio)
    if sesion.scalar(consulta) is not None:
        raise HTTPException(
            status_code=409, detail="Ya existe un grupo de ese tipo con ese nombre en la iglesia."
        )


def crear_grupo(sesion: Session, actor: Usuario, datos: GrupoEntrada) -> GrupoRespuesta:
    _exigir_gestion(sesion, actor, datos.iglesia_id)
    _validar_personas(sesion, datos)
    _validar_nombre_unico(sesion, datos, None)
    grupo = Grupo(
        iglesia_id=datos.iglesia_id,
        tipo=datos.tipo,
        nombre=datos.nombre,
        lider_miembro_id=datos.lider_id,
        asistente_miembro_id=datos.asistente_id,
    )
    sesion.add(grupo)
    sesion.commit()
    sesion.refresh(grupo)
    return _respuesta(grupo)


def actualizar_grupo(
    sesion: Session, actor: Usuario, identificador: int, datos: GrupoEntrada
) -> GrupoRespuesta:
    grupo = _grupo_visible(sesion, actor, identificador)
    if actor.cargo in GESTORES:
        _exigir_gestion(sesion, actor, datos.iglesia_id)
    elif (
        datos.tipo != grupo.tipo
        or datos.iglesia_id != grupo.iglesia_id
        or datos.lider_id != grupo.lider_miembro_id
    ):
        denegar()
    _validar_personas(sesion, datos)
    _validar_nombre_unico(sesion, datos, grupo.id)
    if datos.tipo != grupo.tipo or datos.iglesia_id != grupo.iglesia_id:
        con_integrantes = sesion.scalar(
            select(GrupoMiembro.miembro_id).where(GrupoMiembro.grupo_id == grupo.id)
        )
        if con_integrantes is not None:
            raise HTTPException(
                status_code=409,
                detail="No se puede cambiar el tipo ni la iglesia de un grupo con integrantes.",
            )
    grupo.nombre = datos.nombre
    grupo.tipo = datos.tipo
    grupo.iglesia_id = datos.iglesia_id
    grupo.lider_miembro_id = datos.lider_id
    grupo.asistente_miembro_id = datos.asistente_id
    sesion.commit()
    sesion.refresh(grupo)
    return _respuesta(grupo)
