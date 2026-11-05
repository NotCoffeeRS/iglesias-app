"""Reglas de comunicados (Issue #33, decisiones D9 y D20).

- Presbítero: publica y edita comunicados de cualquier iglesia o de todo el Presbiterio.
- Pastor y apoyo del pastor: solo los de SU iglesia (no los de todo el Presbiterio).
- Todos los cargos ven los comunicados VIGENTES de su iglesia y los de todo el Presbiterio.
- Un comunicado no se borra: vence al pasar su fecha de vigencia.

shortcut: la carga del usuario y las reglas de cargo se repiten de eventos/servicio.py hasta
que se fusione `permisos.py` del PR 56; entonces pasan a una dependencia compartida en
app/seguridad/ para que ningún módulo las copie.
"""

from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.modelos import Comunicado, Iglesia, Usuario
from app.modulos.comunicados.schemas import ComunicadoEntrada, ComunicadoSalida

# shortcut: Mérida es UTC-6 fijo desde que México quitó el horario de verano (2022);
# cambiar a zoneinfo("America/Merida") si eso vuelve a cambiar.
_MERIDA = timezone(timedelta(hours=-6))
_CARGOS_QUE_PUBLICAN = {"pastor", "apoyo_pastor"}


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


def _puede_publicar(usuario: Usuario, iglesia_id: int | None) -> bool:
    if _es_presbitero(usuario):
        return True
    return (
        usuario.cargo in _CARGOS_QUE_PUBLICAN
        and iglesia_id is not None
        and iglesia_id == usuario.iglesia_id
    )


def _puede_ver(usuario: Usuario, comunicado: Comunicado) -> bool:
    return _es_presbitero(usuario) or comunicado.iglesia_id in (None, usuario.iglesia_id)


def _sin_permiso() -> HTTPException:
    return HTTPException(status.HTTP_403_FORBIDDEN, "No tienes permiso para publicar aquí.")


def _salida(comunicado: Comunicado, iglesia_nombre: str | None) -> ComunicadoSalida:
    return ComunicadoSalida(
        id=comunicado.id,
        titulo=comunicado.titulo,
        contenido=comunicado.contenido,
        iglesia_id=comunicado.iglesia_id,
        iglesia_nombre=iglesia_nombre,
        publicado_en=comunicado.publicado_en,
        vigente_hasta=comunicado.vigente_hasta,
        vigente=comunicado.vigente_hasta >= hoy_en_merida(),
    )


def _nombre_iglesia(sesion: Session, iglesia_id: int | None) -> str | None:
    if iglesia_id is None:
        return None
    iglesia = sesion.get(Iglesia, iglesia_id)  # sin consulta si ya se cargó al validar el destino
    return iglesia.nombre if iglesia else None


def _cargar(
    sesion: Session, usuario: Usuario, comunicado_id: int, bloquear: bool = False
) -> Comunicado:
    """El comunicado, o 404 si no existe o la persona no lo puede ver (no se revela cuál).

    `bloquear` toma el candado de la fila hasta confirmar.
    """
    comunicado = sesion.get(Comunicado, comunicado_id, with_for_update=bloquear)
    if comunicado is None or not _puede_ver(usuario, comunicado):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El comunicado no existe.")
    return comunicado


def _validar_publicacion(sesion: Session, usuario: Usuario, datos: ComunicadoEntrada) -> None:
    if datos.vigente_hasta < hoy_en_merida():
        raise HTTPException(422, "La vigencia no puede terminar antes de hoy.")
    if datos.iglesia_id is not None and sesion.get(Iglesia, datos.iglesia_id) is None:
        raise HTTPException(422, "La iglesia no existe.")
    if not _puede_publicar(usuario, datos.iglesia_id):
        raise _sin_permiso()


def _confirmar(sesion: Session, comunicado: Comunicado) -> ComunicadoSalida:
    """Arma la respuesta ANTES de confirmar: así no hay que releer la fila expirada."""
    sesion.flush()
    sesion.refresh(comunicado, ["publicado_en"])  # lo fija la base de datos (now())
    salida = _salida(comunicado, _nombre_iglesia(sesion, comunicado.iglesia_id))
    sesion.commit()
    return salida


def _hay_duplicado(
    sesion: Session, datos: ComunicadoEntrada, excepto_id: int | None = None
) -> bool:
    # shortcut: sin índice único, dos envíos exactamente simultáneos podrían colarse;
    # impedirlo del todo exige una migración (perfil Datos/QA).
    destino = (
        Comunicado.iglesia_id.is_(None)
        if datos.iglesia_id is None
        else Comunicado.iglesia_id == datos.iglesia_id
    )
    return (
        sesion.scalar(
            select(Comunicado.id)
            .where(
                Comunicado.titulo == datos.titulo,
                Comunicado.contenido == datos.contenido,
                Comunicado.vigente_hasta >= hoy_en_merida(),
                Comunicado.id != excepto_id if excepto_id is not None else True,
                destino,
            )
            .limit(1)
        )
        is not None
    )


def listar(sesion: Session, usuario: Usuario) -> list[ComunicadoSalida]:
    """Solo los vigentes que la persona puede ver, del más reciente al más antiguo."""
    consulta = (
        select(Comunicado, Iglesia.nombre)
        .outerjoin(Iglesia, Iglesia.id == Comunicado.iglesia_id)
        .where(Comunicado.vigente_hasta >= hoy_en_merida())
        .order_by(Comunicado.publicado_en.desc(), Comunicado.id.desc())
    )
    if not _es_presbitero(usuario):
        consulta = consulta.where(
            or_(Comunicado.iglesia_id == usuario.iglesia_id, Comunicado.iglesia_id.is_(None))
        )
    return [_salida(comunicado, nombre) for comunicado, nombre in sesion.execute(consulta)]


def obtener(sesion: Session, usuario: Usuario, comunicado_id: int) -> ComunicadoSalida:
    comunicado = _cargar(sesion, usuario, comunicado_id)
    return _salida(comunicado, _nombre_iglesia(sesion, comunicado.iglesia_id))


def publicar(sesion: Session, usuario: Usuario, datos: ComunicadoEntrada) -> ComunicadoSalida:
    _validar_publicacion(sesion, usuario, datos)
    if _hay_duplicado(sesion, datos):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un comunicado igual.")
    comunicado = Comunicado(**datos.model_dump(), creado_por=usuario.id)
    sesion.add(comunicado)
    return _confirmar(sesion, comunicado)


def editar(
    sesion: Session, usuario: Usuario, comunicado_id: int, datos: ComunicadoEntrada
) -> ComunicadoSalida:
    comunicado = _cargar(sesion, usuario, comunicado_id, bloquear=True)
    if not _puede_publicar(usuario, comunicado.iglesia_id):
        raise _sin_permiso()
    if comunicado.vigente_hasta < hoy_en_merida():
        raise HTTPException(status.HTTP_409_CONFLICT, "El comunicado ya venció y no se edita.")
    _validar_publicacion(sesion, usuario, datos)
    if _hay_duplicado(sesion, datos, comunicado.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un comunicado igual.")
    for campo, valor in datos.model_dump().items():
        setattr(comunicado, campo, valor)
    return _confirmar(sesion, comunicado)
