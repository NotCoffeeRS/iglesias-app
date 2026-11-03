import { useEffect, useState } from 'react'
import type { Servicio } from '../../api/asistencia'
import { ErrorApi } from '../../api/cliente'

export function mensajeDeError(error: unknown, accion: string): string {
  if (error instanceof ErrorApi) {
    if (error.estado === 0) return 'No se pudo conectar con el servidor. Revisa tu conexión.'
    if (error.estado === 403) return `No tienes permiso para ${accion}.`
    if (error.estado === 422 || error.estado === 400 || error.estado === 409) return error.message
  }
  return `No se pudo ${accion}. Inténtalo otra vez.`
}

type Carga<T> =
  { tipo: 'cargando' } | { tipo: 'error'; mensaje: string } | { tipo: 'listo'; datos: T }

/** Pide datos al montar (o al cambiar `dependencia`) y permite reintentar. */
export function useCarga<T>(pedir: () => Promise<T>, accion: string, dependencia?: unknown) {
  const [estado, setEstado] = useState<Carga<T>>({ tipo: 'cargando' })
  const [intento, setIntento] = useState(0)

  useEffect(() => {
    let vigente = true
    pedir()
      .then((datos) => vigente && setEstado({ tipo: 'listo', datos }))
      .catch((e) => vigente && setEstado({ tipo: 'error', mensaje: mensajeDeError(e, accion) }))
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

/** Fecha de hoy en Mérida como "AAAA-MM-DD". */
export function hoyEnMerida(): string {
  return new Date().toLocaleDateString('en-CA', { timeZone: 'America/Merida' })
}

/** El domingo sugiere el culto de domingo; los demás días, el de entre semana. */
export function servicioSugerido(fecha: string): Servicio {
  const [a, m, d] = fecha.split('-').map(Number)
  return new Date(a, m - 1, d).getDay() === 0 ? 'culto_domingo' : 'culto_entre_semana'
}

/** "2026-11-01" → "domingo 1 de noviembre" */
export function fechaLarga(fecha: string): string {
  const [a, m, d] = fecha.split('-').map(Number)
  return new Date(a, m - 1, d).toLocaleDateString('es-MX', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })
}

export const claseBotonPrincipal =
  'inline-flex items-center justify-center rounded-xl bg-primario px-5 py-3 font-semibold text-sobre-primario transition-colors hover:bg-primario-hover disabled:cursor-not-allowed disabled:opacity-50'

export const claseCampo =
  'mt-1.5 block w-full rounded-xl border border-borde bg-superficie-2 px-3.5 py-3 text-base text-texto ' +
  'transition-colors focus:border-enlace focus:bg-superficie focus:outline-none focus:ring-2 focus:ring-acento'
