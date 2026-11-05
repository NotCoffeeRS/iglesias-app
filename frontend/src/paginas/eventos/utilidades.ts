import { useEffect, useState } from 'react'
import { ErrorApi, esRutaInexistente } from '../../api/cliente'

export function mensajeDeError(error: unknown, accion: string): string {
  if (error instanceof ErrorApi) {
    if (esRutaInexistente(error)) return 'Esta función todavía no está disponible.'
    if (error.estado === 0) return 'No se pudo conectar con el servidor. Revisa tu conexión.'
    if (error.estado === 403) return `No tienes permiso para ${accion}.`
    if (error.estado === 404) return 'Este evento ya no existe. Recarga la página.'
    if (error.estado === 409) return error.message
    if (error.estado === 422 || error.estado === 400) return error.message
  }
  return `No se pudo ${accion}. Inténtalo otra vez.`
}

type Carga<T> =
  { tipo: 'cargando' } | { tipo: 'error'; mensaje: string } | { tipo: 'listo'; datos: T }

type Guardada<T> = { clave: string } & Carga<T>

/** Pide datos al montar y cada vez que cambia `clave`; "reintentar" vuelve a pedirlos. */
export function useCarga<T>(pedir: () => Promise<T>, accion: string, clave: string) {
  const [guardada, setGuardada] = useState<Guardada<T>>({ clave: '', tipo: 'cargando' })
  const [intento, setIntento] = useState(0)

  useEffect(() => {
    let vigente = true
    pedir()
      .then((datos) => vigente && setGuardada({ clave, tipo: 'listo', datos }))
      .catch(
        (e) => vigente && setGuardada({ clave, tipo: 'error', mensaje: mensajeDeError(e, accion) }),
      )
    return () => {
      vigente = false
    }
    // `pedir` cambia en cada render; se vuelve a pedir solo por `clave` o al reintentar.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intento, clave])

  const estado: Carga<T> = guardada.clave === clave ? guardada : { tipo: 'cargando' }

  function reintentar() {
    setGuardada({ clave: '', tipo: 'cargando' })
    setIntento((n) => n + 1)
  }

  return { estado, reintentar }
}

export function hoyEnMerida(): string {
  return new Date().toLocaleDateString('en-CA', { timeZone: 'America/Merida' })
}

/** "2026-11-01" → "domingo 1 de noviembre de 2026" */
export function fechaLarga(fecha: string): string {
  const [a, m, d] = fecha.split('-').map(Number)
  return new Date(a, m - 1, d).toLocaleDateString('es-MX', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

/** "19:30:00" → "19:30" */
export function horaCorta(hora: string): string {
  return hora.slice(0, 5)
}

export const claseBotonPrincipal =
  'inline-flex items-center justify-center rounded-xl bg-primario px-5 py-2.5 font-semibold text-sobre-primario transition-colors hover:bg-primario-hover disabled:cursor-not-allowed disabled:opacity-50'

export const claseBotonSecundario =
  'inline-flex items-center justify-center rounded-xl border border-borde bg-superficie px-5 py-2.5 font-semibold text-texto transition-colors hover:bg-superficie-2'

export const claseCampo =
  'mt-1.5 block w-full rounded-xl border border-borde bg-superficie-2 px-3.5 py-3 text-base text-texto ' +
  'transition-colors focus:border-enlace focus:bg-superficie focus:outline-none focus:ring-2 focus:ring-acento ' +
  'aria-invalid:border-peligro disabled:opacity-60'
