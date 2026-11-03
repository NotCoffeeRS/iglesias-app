"""Comprobación de que el proceso de la API responde."""

from fastapi import APIRouter

router = APIRouter(tags=["salud"])


@router.get("/salud")
def salud() -> dict[str, str]:
    return {"estado": "ok"}
