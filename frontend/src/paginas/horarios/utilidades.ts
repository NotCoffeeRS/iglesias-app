import { useEffect, useState } from 'react'
import { ErrorApi, esRutaInexistente } from '../../api/cliente'
import { TIPOS, type Horario } from '../../api/horarios'

export function mensajeDeError(error: unknown, accion: string): string {
  if (error instanceof ErrorApi) {
    if (esRutaInexistente(error)) return 'Esta función todavía no está disponible.'
    if (error.estado === 0) return 'No se pudo conectar con el servidor. Revisa tu conexión.'
    if (error.estado === 403) return `No tienes permiso para ${accion}.`
    if (error.estado === 404) return 'Ese horario o sede ya no existe. Recarga la página.'
    // 409: el servidor responde que el horario ya existe (misma sede, tipo, día y hora) o que
    // sus datos relacionados cambiaron.
    if (error.estado === 409)
      return 'Ya existe un horario igual (misma sede, tipo, día y hora), o los datos cambiaron. Revisa lo escrito; si sigue igual, recarga la página.'
    if (error.estado === 422 || error.estado === 400) return error.message
  }
  return `No se pudo ${accion}. Inténtalo otra vez.`
}

type Carga<T> =
  { tipo: 'cargando' } | { tipo: 'error'; mensaje: string } | { tipo: 'listo'; datos: T }

/** Pide datos al montar (o al cambiar `dependencia`) y permite reintentar o recargar. */
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
    // `pedir` cambia en cada render; se vuelve a pedir solo por `dependencia` o al recargar.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intento, dependencia])

  /** Vuelve a pedir; con `silencioso` conserva los datos actuales mientras llega la respuesta. */
  function recargar(silencioso = false) {
    if (!silencioso) setEstado({ tipo: 'cargando' })
    setIntento((n) => n + 1)
  }

  return { estado, recargar }
}

/** "19:30" o "19:30:00" → { hora: "7:30", periodo: "p.m." } */
function partirHora(hora: string): { hora: string; periodo: string } | null {
  const [h, m] = hora.split(':').map(Number)
  if (Number.isNaN(h) || Number.isNaN(m)) return null
  return {
    hora: `${h % 12 || 12}:${String(m).padStart(2, '0')}`,
    periodo: h < 12 ? 'a.m.' : 'p.m.',
  }
}

/** "7:30 p.m.", o "7:30 – 9:00 p.m." si ambas horas son del mismo periodo. */
export function rangoHora({ hora_inicio, hora_fin }: Pick<Horario, 'hora_inicio' | 'hora_fin'>) {
  const inicio = partirHora(hora_inicio)
  if (!inicio) return hora_inicio
  const fin = hora_fin ? partirHora(hora_fin) : null
  if (!fin) return `${inicio.hora} ${inicio.periodo}`
  return inicio.periodo === fin.periodo
    ? `${inicio.hora} – ${fin.hora} ${fin.periodo}`
    : `${inicio.hora} ${inicio.periodo} – ${fin.hora} ${fin.periodo}`
}

export function nombreTipo(clave: string): string {
  return TIPOS.find((t) => t.clave === clave)?.nombre ?? clave
}

export const claseBotonPrincipal =
  'inline-flex items-center justify-center rounded-xl bg-primario px-5 py-2.5 font-semibold text-sobre-primario transition-colors hover:bg-primario-hover disabled:cursor-not-allowed disabled:opacity-50'

export const claseBotonSecundario =
  'inline-flex items-center justify-center rounded-xl border border-borde bg-superficie px-4 py-2.5 font-semibold text-texto transition-colors hover:bg-superficie-2'

export const claseCampo =
  'mt-1.5 block w-full rounded-xl border border-borde bg-superficie-2 px-3.5 py-3 text-base text-texto ' +
  'transition-colors focus:border-enlace focus:bg-superficie focus:outline-none focus:ring-2 focus:ring-acento ' +
  'aria-invalid:border-peligro'
