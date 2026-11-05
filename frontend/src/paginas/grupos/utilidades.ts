import { useEffect, useState } from 'react'
import { ErrorApi, esRutaInexistente } from '../../api/cliente'
import { TIPOS_GRUPO, type TipoGrupo } from '../../api/grupos'

export function mensajeDeError(error: unknown, accion: string): string {
  if (error instanceof ErrorApi) {
    if (esRutaInexistente(error)) return 'Esta función todavía no está disponible.'
    if (error.estado === 0) return 'No se pudo conectar con el servidor. Revisa tu conexión.'
    if (error.estado === 403) return `No tienes permiso para ${accion}.`
    if (error.estado === 404) return 'Este grupo no existe o no está en tu alcance.'
    // 409: nombre repetido o cambio no permitido con integrantes; el servidor manda el motivo.
    if (error.estado === 409 || error.estado === 422 || error.estado === 400) return error.message
  }
  return `No se pudo ${accion}. Inténtalo otra vez.`
}

type Carga<T> =
  | { tipo: 'cargando' }
  | { tipo: 'error'; mensaje: string; sinPermiso: boolean }
  | { tipo: 'listo'; datos: T }

/** Pide datos al montar (o al cambiar `dependencia`) y permite reintentar. */
export function useCarga<T>(pedir: () => Promise<T>, accion: string, dependencia?: unknown) {
  const [estado, setEstado] = useState<Carga<T>>({ tipo: 'cargando' })
  const [intento, setIntento] = useState(0)

  useEffect(() => {
    let vigente = true
    pedir()
      .then((datos) => vigente && setEstado({ tipo: 'listo', datos }))
      .catch(
        (e) =>
          vigente &&
          setEstado({
            tipo: 'error',
            mensaje: mensajeDeError(e, accion),
            sinPermiso: e instanceof ErrorApi && e.estado === 403,
          }),
      )
    return () => {
      vigente = false
    }
    // `pedir` cambia en cada render; se vuelve a pedir solo por `dependencia` o al reintentar.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intento, dependencia])

  function reintentar() {
    setEstado({ tipo: 'cargando' })
    setIntento((n) => n + 1)
  }

  return { estado, reintentar }
}

export function nombreTipo(clave: TipoGrupo): string {
  return TIPOS_GRUPO.find((t) => t.clave === clave)?.nombre ?? clave
}

export const claseBotonPrincipal =
  'inline-flex items-center justify-center rounded-xl bg-primario px-5 py-2.5 font-semibold text-sobre-primario transition-colors hover:bg-primario-hover disabled:cursor-not-allowed disabled:opacity-50'

export const claseBotonSecundario =
  'inline-flex items-center justify-center rounded-xl border border-borde bg-superficie px-5 py-2.5 font-semibold text-texto transition-colors hover:bg-resalte'

export const claseCampo =
  'mt-1.5 block w-full rounded-xl border border-borde bg-superficie-2 px-3.5 py-3 text-base text-texto ' +
  'transition-colors focus:border-enlace focus:bg-superficie focus:outline-none focus:ring-2 focus:ring-acento ' +
  'aria-invalid:border-peligro disabled:opacity-60'
