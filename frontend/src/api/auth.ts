// Sesión: inicio y cierre. Todo lo que depende del contrato de la API de login (#7) está aquí.
//
// PENDIENTE de confirmar con el #7: ruta, formato del cuerpo (JSON) y nombre del campo del token.
// Si cambia, solo se ajusta este archivo.

import { api, borrarToken, guardarToken, obtenerToken } from './cliente'

const RUTA_LOGIN = '/auth/login'

interface RespuestaLogin {
  access_token: string
  token_type: string
}

/** Pide el token a la API y lo guarda. Lanza `ErrorApi` si falla (401 = credenciales inválidas). */
export async function iniciarSesion(usuario: string, contrasena: string): Promise<void> {
  const respuesta = await api.post<RespuestaLogin>(RUTA_LOGIN, { usuario, contrasena })
  guardarToken(respuesta.access_token)
}

export function cerrarSesion(): void {
  borrarToken()
}

export function haySesion(): boolean {
  return obtenerToken() !== null
}
