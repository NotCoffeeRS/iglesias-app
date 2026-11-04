import { useEffect, useState } from 'react'
import { ErrorApi } from '../../api/cliente'
import { ETIQUETAS, type Partida } from '../../api/reporte_financiero'

export function mensajeDeError(error: unknown, accion: string): string {
  if (error instanceof ErrorApi) {
    if (error.estado === 0) return 'No se pudo conectar con el servidor. Revisa tu conexión.'
    if (error.estado === 403) return `No tienes permiso para ${accion}.`
    if (error.estado === 422 || error.estado === 400) return error.message
  }
  return `No se pudo ${accion}. Inténtalo otra vez.`
}

export function esSinAcceso(error: unknown): boolean {
  return error instanceof ErrorApi && error.estado === 403
}

type Estado<T> =
  | { tipo: 'cargando' }
  | { tipo: 'error'; mensaje: string; sinAcceso: boolean }
  | { tipo: 'listo'; datos: T; actualizando: boolean }

type Guardada<T> =
  | { clave: string; tipo: 'error'; mensaje: string; sinAcceso: boolean }
  | { clave: string; tipo: 'listo'; datos: T }
  | { clave: ''; tipo: 'cargando' }

/**
 * Pide datos al montar y cada vez que cambia `clave`. Al cambiar de filtro conserva lo que ya se
 * mostraba y lo marca como `actualizando` (para atenuarlo), en lugar de borrarlo con un esqueleto.
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

  let estado: Estado<T>
  if (guardada.tipo === 'cargando') estado = { tipo: 'cargando' }
  else if (guardada.tipo === 'error')
    estado =
      guardada.clave === clave
        ? { tipo: 'error', mensaje: guardada.mensaje, sinAcceso: guardada.sinAcceso }
        : { tipo: 'cargando' }
  else estado = { tipo: 'listo', datos: guardada.datos, actualizando: guardada.clave !== clave }

  function reintentar() {
    setGuardada({ clave: '', tipo: 'cargando' })
    setIntento((n) => n + 1)
  }

  return { estado, reintentar }
}

// ---- Dinero: todo se maneja en CENTAVOS enteros para no arrastrar errores de decimales ----

/** "1500.50", "-120.5" o 1500.5 → centavos (puede ser negativo). null si no es un monto válido. */
export function aCentavos(valor: string | number): number | null {
  if (typeof valor === 'number') return Number.isFinite(valor) ? Math.round(valor * 100) : null
  const m = valor.trim().match(/^(-?)(\d+)(?:\.(\d{1,2}))?$/)
  if (!m) return null
  const centavos = Number(m[2]) * 100 + Number((m[3] ?? '').padEnd(2, '0'))
  return m[1] ? -centavos : centavos
}

const formatoMoneda = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' })

/** 150050 → "$1,500.50"; -12050 → "-$120.50" */
export function formatearMonto(centavos: number): string {
  return formatoMoneda.format(centavos / 100)
}

/** Monto del servidor ya en pesos con formato; un valor ilegible cuenta como $0.00. */
export function montoATexto(valor: string | number): string {
  return formatearMonto(aCentavos(valor) ?? 0)
}

/** Partidas listas para dibujar: con nombre, en centavos, sin ceros y de mayor a menor. */
export function prepararPartidas(partidas: Partida[]) {
  return partidas
    .map((p) => ({
      clave: p.clave,
      nombre: p.nombre || ETIQUETAS[p.clave] || p.clave,
      centavos: aCentavos(p.monto) ?? 0,
    }))
    .filter((p) => p.centavos > 0)
    .sort((a, b) => b.centavos - a.centavos)
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

export const claseBotonPrincipal =
  'inline-flex items-center justify-center rounded-xl bg-primario px-5 py-2.5 font-semibold text-sobre-primario transition-colors hover:bg-primario-hover disabled:cursor-not-allowed disabled:opacity-50'

export const claseCampo =
  'mt-1.5 block w-full rounded-xl border border-borde bg-superficie-2 px-3.5 py-3 text-base text-texto ' +
  'transition-colors focus:border-enlace focus:bg-superficie focus:outline-none focus:ring-2 focus:ring-acento'
