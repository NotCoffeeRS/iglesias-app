"""Funciones compartidas para guardar y comprobar hashes Argon2id."""

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

_password_hash = PasswordHash.recommended()


def crear_hash(contrasena: str) -> str:
    """Devuelve un hash con sal aleatoria; nunca registra la contraseña."""
    return _password_hash.hash(contrasena)


def verificar_contrasena(contrasena: str, hash_guardado: str) -> bool:
    """Un hash desconocido o inválido no autentica al usuario."""
    try:
        return _password_hash.verify(contrasena, hash_guardado)
    except (UnknownHashError, ValueError):
        return False
