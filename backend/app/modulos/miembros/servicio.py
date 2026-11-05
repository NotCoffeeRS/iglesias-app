"""Alcance y operaciones de miembros (#17), según AGENTS.md §9 y las decisiones D9, D14, D20 y D21.

Quién ve a quién:
- Presbítero: todos los miembros del Presbiterio.
- Pastor y apoyo del pastor: los de su iglesia.
- Tesorero: ninguno (D20, regla 3).
- Cualquier otro cargo: solo los integrantes de los grupos que dirige su ficha de miembro (D21).

Quién registra y edita: presbítero, pastor y apoyo, y solo dentro de su iglesia (D20, regla 5).
"""

import unicodedata
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy import Select, false, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Grupo, GrupoMiembro, Iglesia, Miembro, Usuario
from app.modulos.miembros.schemas import MiembroEntrada, MiembroResumen
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
    return HTTPException(status_code=404, detail="Este miembro no existe o no está en tu alcance.")


def normalizar(texto: str) -> str:
    """Compara sin acentos ni mayúsculas: "jose" encuentra a "José"."""
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).casefold().strip()


def _visibles(actor: Usuario) -> Select:
    """Miembros que `actor` puede ver, junto con el nombre de su iglesia."""
    if actor.cargo == "tesorero":
        denegar()
    consulta = select(Miembro, Iglesia.nombre).join(Iglesia, Iglesia.id == Miembro.iglesia_id)
    if actor.cargo == "presbitero":
        return consulta
    if actor.cargo in GESTORES:
        return consulta.where(Miembro.iglesia_id == actor.iglesia_id)
    if actor.miembro_id is None:
        return consulta.where(false())
    dirigidos = select(Grupo.id).where(
        Grupo.lider_miembro_id == actor.miembro_id,
        Grupo.activo.is_(True),
        Grupo.iglesia_id == actor.iglesia_id,
    )
    integrantes = select(GrupoMiembro.miembro_id).where(GrupoMiembro.grupo_id.in_(dirigidos))
    return consulta.where(Miembro.id.in_(integrantes), Miembro.iglesia_id == actor.iglesia_id)


def consultar(
    sesion: Session,
    actor: Usuario,
    *,
    estado: str | None = None,
    iglesia_id: int | None = None,
    texto: str | None = None,
) -> list[MiembroResumen]:
    consulta = _visibles(actor)
    if estado is not None:
        consulta = consulta.where(Miembro.estado == estado)
    if iglesia_id is not None:
        consulta = consulta.where(Miembro.iglesia_id == iglesia_id)
    aguja = normalizar(texto) if texto else ""
    resultado = [
        MiembroResumen(
            id=miembro.id,
            nombre=miembro.nombre,
            telefono=miembro.telefono,
            estado=miembro.estado,
            iglesia_id=miembro.iglesia_id,
            iglesia_nombre=nombre_iglesia,
        )
        for miembro, nombre_iglesia in sesion.execute(consulta).all()
        if not aguja or aguja in normalizar(miembro.nombre)
    ]
    return sorted(resultado, key=lambda m: (normalizar(m.nombre), m.id))


def obtener_miembro(sesion: Session, actor: Usuario, identificador: int) -> Miembro:
    fila = sesion.execute(_visibles(actor).where(Miembro.id == identificador)).first()
    if fila is None:
        raise no_encontrado()
    return fila[0]


def _exigir_escritura(sesion: Session, actor: Usuario, iglesia_id: int) -> None:
    if actor.cargo not in GESTORES:
        denegar()
    if actor.cargo != "presbitero" and iglesia_id != actor.iglesia_id:
        denegar()
    if sesion.get(Iglesia, iglesia_id) is None:
        raise HTTPException(status_code=422, detail="La iglesia indicada no existe.")


def _exigir_que_pueda_cambiar_de_iglesia(sesion: Session, miembro: Miembro) -> None:
    """Quien está en grupos o tiene cuenta ligada no cambia de iglesia: se mezclarían alcances."""
    en_grupo = sesion.scalar(
        select(GrupoMiembro.grupo_id).where(GrupoMiembro.miembro_id == miembro.id)
    )
    dirige = sesion.scalar(
        select(Grupo.id).where(
            (Grupo.lider_miembro_id == miembro.id) | (Grupo.asistente_miembro_id == miembro.id)
        )
    )
    con_cuenta = sesion.scalar(select(Usuario.id).where(Usuario.miembro_id == miembro.id))
    if en_grupo is not None or dirige is not None or con_cuenta is not None:
        raise HTTPException(
            status_code=409,
            detail="No se puede cambiar de iglesia a quien está en grupos o tiene cuenta ligada.",
        )


def crear_miembro(sesion: Session, actor: Usuario, datos: MiembroEntrada) -> Miembro:
    _exigir_escritura(sesion, actor, datos.iglesia_id)
    miembro = Miembro(**datos.model_dump())
    sesion.add(miembro)
    sesion.commit()
    sesion.refresh(miembro)
    return miembro


def actualizar_miembro(
    sesion: Session, actor: Usuario, identificador: int, datos: MiembroEntrada
) -> Miembro:
    if actor.cargo not in GESTORES:
        denegar()
    miembro = obtener_miembro(sesion, actor, identificador)
    _exigir_escritura(sesion, actor, datos.iglesia_id)
    if datos.iglesia_id != miembro.iglesia_id:
        _exigir_que_pueda_cambiar_de_iglesia(sesion, miembro)
    for campo, valor in datos.model_dump().items():
        setattr(miembro, campo, valor)
    sesion.commit()
    sesion.refresh(miembro)
    return miembro
