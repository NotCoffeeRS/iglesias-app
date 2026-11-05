"""Reglas de eventos (Issue #32, decisiones D9 y D20).

- Presbítero: ve, crea, edita y cancela eventos de cualquier iglesia o de todo el Presbiterio.
- Pastor y apoyo del pastor: solo los de SU iglesia (no los de todo el Presbiterio).
- Los demás cargos: solo ven los de su iglesia y los de todo el Presbiterio.
- Un evento no se borra: se cancela.
"""

from datetime import UTC, date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.modelos import Evento, Iglesia, Usuario
from app.modulos.eventos.schemas import EventoEntrada, EventoSalida

# shortcut: Mérida es UTC-6 fijo desde que México quitó el horario de verano (2022);
# cambiar a zoneinfo("America/Merida") si eso vuelve a cambiar.
_MERIDA = timezone(timedelta(hours=-6))
_CARGOS_QUE_ADMINISTRAN = {"pastor", "apoyo_pastor"}


def hoy_en_merida() -> date:
    return datetime.now(_MERIDA).date()


def _sesion_invalida() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesión no válida o vencida",
        headers={"WWW-Authenticate": "Bearer"},
    )


def usuario_actual(sesion: Session, usuario_id: str) -> Usuario:
    """Carga la cuenta del token; una cuenta desactivada o inexistente no tiene sesión."""
    try:
        cuenta = sesion.get(Usuario, int(usuario_id))
    except ValueError:
        raise _sesion_invalida() from None
    if cuenta is None or not cuenta.activo:
        raise _sesion_invalida()
    return cuenta


def _es_presbitero(usuario: Usuario) -> bool:
    return usuario.cargo == "presbitero"


def _puede_administrar(usuario: Usuario, iglesia_id: int | None) -> bool:
    if _es_presbitero(usuario):
        return True
    return (
        usuario.cargo in _CARGOS_QUE_ADMINISTRAN
        and iglesia_id is not None
        and iglesia_id == usuario.iglesia_id
    )


def _puede_ver(usuario: Usuario, evento: Evento) -> bool:
    return _es_presbitero(usuario) or evento.iglesia_id in (None, usuario.iglesia_id)


def _sin_permiso() -> HTTPException:
    return HTTPException(
        status.HTTP_403_FORBIDDEN, "No tienes permiso para administrar este evento."
    )


def _no_existe() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "El evento no existe.")


def _salida(evento: Evento, iglesia_nombre: str | None) -> EventoSalida:
    return EventoSalida(
        id=evento.id,
        titulo=evento.titulo,
        fecha=evento.fecha,
        hora=evento.hora,
        iglesia_id=evento.iglesia_id,
        iglesia_nombre=iglesia_nombre,
        lugar=evento.lugar,
        descripcion=evento.descripcion,
        cancelado=evento.cancelado_en is not None,
    )


def _nombre_iglesia(sesion: Session, iglesia_id: int | None) -> str | None:
    if iglesia_id is None:
        return None
    return sesion.scalar(select(Iglesia.nombre).where(Iglesia.id == iglesia_id))


def _cargar(sesion: Session, usuario: Usuario, evento_id: int) -> Evento:
    """El evento, o 404 si no existe o la persona no lo puede ver (no se revela cuál)."""
    evento = sesion.get(Evento, evento_id)
    if evento is None or not _puede_ver(usuario, evento):
        raise _no_existe()
    return evento


def _validar_destino(sesion: Session, usuario: Usuario, iglesia_id: int | None) -> None:
    if iglesia_id is not None and sesion.get(Iglesia, iglesia_id) is None:
        raise HTTPException(422, "La iglesia no existe.")
    if not _puede_administrar(usuario, iglesia_id):
        raise _sin_permiso()


def listar(
    sesion: Session, usuario: Usuario, desde: date | None, iglesia_id: int | None
) -> list[EventoSalida]:
    if iglesia_id is not None and not _es_presbitero(usuario) and iglesia_id != usuario.iglesia_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No tienes permiso para ver esa iglesia.")
    consulta = (
        select(Evento, Iglesia.nombre)
        .outerjoin(Iglesia, Iglesia.id == Evento.iglesia_id)
        .where(Evento.fecha >= (desde or hoy_en_merida()))
        .order_by(Evento.fecha, Evento.hora, Evento.id)
    )
    if iglesia_id is not None:
        consulta = consulta.where(or_(Evento.iglesia_id == iglesia_id, Evento.iglesia_id.is_(None)))
    elif not _es_presbitero(usuario):
        consulta = consulta.where(
            or_(Evento.iglesia_id == usuario.iglesia_id, Evento.iglesia_id.is_(None))
        )
    return [_salida(evento, nombre) for evento, nombre in sesion.execute(consulta)]


def obtener(sesion: Session, usuario: Usuario, evento_id: int) -> EventoSalida:
    evento = _cargar(sesion, usuario, evento_id)
    return _salida(evento, _nombre_iglesia(sesion, evento.iglesia_id))


def crear(sesion: Session, usuario: Usuario, datos: EventoEntrada) -> EventoSalida:
    if datos.fecha < hoy_en_merida():
        raise HTTPException(422, "La fecha no puede ser anterior a hoy.")
    _validar_destino(sesion, usuario, datos.iglesia_id)
    evento = Evento(**datos.model_dump(), creado_por=usuario.id)
    sesion.add(evento)
    sesion.commit()
    return _salida(evento, _nombre_iglesia(sesion, evento.iglesia_id))


def editar(sesion: Session, usuario: Usuario, evento_id: int, datos: EventoEntrada) -> EventoSalida:
    evento = _cargar(sesion, usuario, evento_id)
    if not _puede_administrar(usuario, evento.iglesia_id):
        raise _sin_permiso()
    if evento.cancelado_en is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "El evento está cancelado y no se edita.")
    _validar_destino(sesion, usuario, datos.iglesia_id)
    for campo, valor in datos.model_dump().items():
        setattr(evento, campo, valor)
    sesion.commit()
    return _salida(evento, _nombre_iglesia(sesion, evento.iglesia_id))


def cancelar(sesion: Session, usuario: Usuario, evento_id: int) -> EventoSalida:
    evento = _cargar(sesion, usuario, evento_id)
    if not _puede_administrar(usuario, evento.iglesia_id):
        raise _sin_permiso()
    if evento.cancelado_en is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "El evento ya estaba cancelado.")
    evento.cancelado_en = datetime.now(UTC)
    sesion.commit()
    return _salida(evento, _nombre_iglesia(sesion, evento.iglesia_id))
