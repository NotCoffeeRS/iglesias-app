import { useEffect, useState } from 'react'
import { ErrorApi, esRutaInexistente } from '../../api/cliente'
import { CATEGORIAS, type Categoria } from '../../api/gastos'

export function mensajeDeError(error: unknown, accion: string): string {
  if (error instanceof ErrorApi) {
    if (esRutaInexistente(error)) return 'Esta función todavía no está disponible.'
    if (error.estado === 0) return 'No se pudo conectar con el servidor. Revisa tu conexión.'
    if (error.estado === 403) return `No tienes permiso para ${accion}.`
    if (error.estado === 404) return 'Este gasto ya no existe. Recarga la página.'
    if (error.estado === 409) return 'Este gasto ya estaba anulado.'
    if (error.estado === 422 || error.estado === 400) return error.message
  }
  return `No se pudo ${accion}. Inténtalo otra vez.`
}

export function esSinAcceso(error: unknown): boolean {
  return error instanceof ErrorApi && error.estado === 403
}

type Carga<T> =
  | { tipo: 'cargando' }
  | { tipo: 'error'; mensaje: string; sinAcceso: boolean }
  | { tipo: 'listo'; datos: T }

type Guardada<T> = { clave: string } & Carga<T>

/**
 * Pide datos al montar y cada vez que cambia `clave`. Mientras llegan los nuevos, muestra
 * "cargando" en lugar de los datos del filtro anterior (para no mezclar totales de otro periodo).
 */
export function useCarga<T>(pedir: () => Promise<T>, accion: string, clave: string) {
  const [guardada, setGuardada] = useState<Guardada<T>>({ clave: '', tipo: 'cargando' })
  const [intento, setIntento] = useState(0)

  useEffect(() => {
    let vigente = true
    pedir()
      .then((datos) => vigente && setGuardada({ clave, tipo: 'listo', datos }))
      .catch(
        (e) =>
          vigente &&
          setGuardada({
            clave,
            tipo: 'error',
            mensaje: mensajeDeError(e, accion),
            sinAcceso: esSinAcceso(e),
          }),
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

// ---- Dinero: todo se maneja en CENTAVOS enteros para no arrastrar errores de decimales ----

/** "1500.50" o 1500.5 → 150050. Devuelve null si no es un monto válido. */
export function aCentavos(valor: string | number): number | null {
  if (typeof valor === 'number') return Number.isFinite(valor) ? Math.round(valor * 100) : null
  const m = valor.trim().match(/^(\d+)(?:\.(\d{1,2}))?$/)
  if (!m) return null
  return Number(m[1]) * 100 + Number((m[2] ?? '').padEnd(2, '0'))
}

/** Lo que escribe la persona: acepta "1,500.5", "$ 1500" y "1500.50". */
export function leerMonto(texto: string): number | null {
  return aCentavos(texto.replace(/[$,\s]/g, ''))
}

/** 150050 → "1500.50" (el formato que recibe el servidor). */
export function aTextoMonto(centavos: number): string {
  const enteros = Math.floor(centavos / 100)
  return `${enteros}.${String(centavos % 100).padStart(2, '0')}`
}

const formatoMoneda = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' })

/** 150050 → "$1,500.50" */
export function formatearMonto(centavos: number): string {
  return formatoMoneda.format(centavos / 100)
}

// ---- Fechas (en la zona horaria de Mérida) ----

export function hoyEnMerida(): string {
  return new Date().toLocaleDateString('en-CA', { timeZone: 'America/Merida' })
}

function ymd(a: number, m: number, d: number): string {
  return `${a}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
}

export type Periodo = 'mes' | 'mes_pasado' | 'anio' | 'otro'

export function rangoDe(
  periodo: Exclude<Periodo, 'otro'>,
  hoy: string,
): { desde: string; hasta: string } {
  const [a, m] = hoy.split('-').map(Number)
  if (periodo === 'mes') return { desde: ymd(a, m, 1), hasta: hoy }
  if (periodo === 'anio') return { desde: ymd(a, 1, 1), hasta: hoy }
  const pa = m === 1 ? a - 1 : a
  const pm = m === 1 ? 12 : m - 1
  return { desde: ymd(pa, pm, 1), hasta: ymd(pa, pm, new Date(pa, pm, 0).getDate()) }
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

export function nombreCategoria(clave: Categoria): string {
  return CATEGORIAS.find((c) => c.clave === clave)?.nombre ?? clave
}

export const claseBotonPrincipal =
  'inline-flex items-center justify-center rounded-xl bg-primario px-5 py-2.5 font-semibold text-sobre-primario transition-colors hover:bg-primario-hover disabled:cursor-not-allowed disabled:opacity-50'

export const claseBotonSecundario =
  'inline-flex items-center justify-center rounded-xl border border-borde bg-superficie px-5 py-2.5 font-semibold text-texto transition-colors hover:bg-superficie-2'

export const claseCampo =
  'mt-1.5 block w-full rounded-xl border border-borde bg-superficie-2 px-3.5 py-3 text-base text-texto ' +
  'transition-colors focus:border-enlace focus:bg-superficie focus:outline-none focus:ring-2 focus:ring-acento ' +
  'aria-invalid:border-peligro disabled:opacity-60'
