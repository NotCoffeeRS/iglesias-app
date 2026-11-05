"""Categorías por edad cumplida y acceso de gestores a su iglesia."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modelos import Iglesia, Menor, Tutor, Usuario
from app.modulos.menores.schemas import MenorEntrada
from app.seguridad.permisos import validar_alcance


def hoy_en_merida() -> date:
    return datetime.now(ZoneInfo("America/Merida")).date()


def edad_cumplida(nacimiento: date, hoy: date) -> int:
    return hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))


def categoria(edad: int, sexo: str) -> str | None:
    if 4 <= edad <= 11:
        return "nina" if sexo == "femenino" else "nino"
    return "adolescente" if 12 <= edad <= 17 else None


def validar_edad(nacimiento: date):
    if not 4 <= edad_cumplida(nacimiento, hoy_en_merida()) <= 17:
        raise HTTPException(
            status_code=422, detail="La edad debe estar entre 4 y 17 años cumplidos."
        )


def resumen(menor: Menor, iglesia_nombre: str):
    edad = edad_cumplida(menor.fecha_nacimiento, hoy_en_merida())
    return {
        "id": menor.id,
        "iglesia_id": menor.iglesia_id,
        "iglesia_nombre": iglesia_nombre,
        "nombre": menor.nombre,
        "fecha_nacimiento": menor.fecha_nacimiento,
        "sexo": menor.sexo,
        "edad": edad,
        "categoria": categoria(edad, menor.sexo),
        "activo": menor.activo,
    }


def listar_menores(sesion: Session, actor: Usuario, iglesia_id: int | None):
    consulta = select(Menor, Iglesia.nombre).join(Iglesia, Iglesia.id == Menor.iglesia_id)
    if iglesia_id is not None:
        validar_alcance(sesion, actor, iglesia_id)
        consulta = consulta.where(Menor.iglesia_id == iglesia_id)
    if actor.cargo != "presbitero":
        consulta = consulta.where(Menor.iglesia_id == actor.iglesia_id)
    return [
        resumen(m, nombre)
        for m, nombre in sesion.execute(consulta.order_by(Menor.nombre, Menor.id))
    ]


def obtener_menor(sesion: Session, actor: Usuario, identificador: int) -> Menor:
    consulta = select(Menor).where(Menor.id == identificador)
    if actor.cargo != "presbitero":
        consulta = consulta.where(Menor.iglesia_id == actor.iglesia_id)
    menor = sesion.scalar(consulta)
    if menor is None:
        raise HTTPException(
            status_code=404, detail="El registro no existe o no está en tu alcance."
        )
    return menor


def respuesta(sesion: Session, menor: Menor):
    iglesia = sesion.get(Iglesia, menor.iglesia_id)
    return {
        **resumen(menor, iglesia.nombre),
        "direccion": menor.direccion,
        "tutores": list(
            sesion.scalars(select(Tutor).where(Tutor.menor_id == menor.id).order_by(Tutor.id))
        ),
    }


def obtener_iglesia(sesion: Session, actor: Usuario, iglesia_id: int):
    validar_alcance(sesion, actor, iglesia_id)
    if sesion.get(Iglesia, iglesia_id) is None:
        raise HTTPException(status_code=422, detail="La iglesia indicada no existe.")


def guardar(sesion: Session):
    try:
        sesion.commit()
    except IntegrityError as error:
        sesion.rollback()
        raise HTTPException(
            status_code=409, detail="Los datos relacionados cambiaron. Recarga la página."
        ) from error


def crear_menor(sesion: Session, actor: Usuario, datos: MenorEntrada):
    obtener_iglesia(sesion, actor, datos.iglesia_id)
    validar_edad(datos.fecha_nacimiento)
    menor = Menor(**datos.model_dump(exclude={"tutores"}))
    try:
        sesion.add(menor)
        sesion.flush()
        sesion.add_all([Tutor(menor_id=menor.id, **t.model_dump()) for t in datos.tutores])
        guardar(sesion)
    except IntegrityError as error:
        sesion.rollback()
        raise HTTPException(
            status_code=409, detail="No se pudo guardar el registro completo."
        ) from error
    return respuesta(sesion, menor)


def actualizar_menor(sesion: Session, actor: Usuario, identificador: int, datos: MenorEntrada):
    menor = obtener_menor(sesion, actor, identificador)
    sesion.refresh(menor, with_for_update=True)
    obtener_iglesia(sesion, actor, datos.iglesia_id)
    validar_edad(datos.fecha_nacimiento)
    tutores = list(sesion.scalars(select(Tutor).where(Tutor.menor_id == menor.id)))
    for campo, valor in datos.model_dump(exclude={"tutores"}).items():
        setattr(menor, campo, valor)
    for tutor in tutores:
        sesion.delete(tutor)
    sesion.add_all([Tutor(menor_id=menor.id, **t.model_dump()) for t in datos.tutores])
    guardar(sesion)
    return respuesta(sesion, menor)
