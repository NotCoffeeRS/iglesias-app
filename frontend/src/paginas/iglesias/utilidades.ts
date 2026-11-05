import { useEffect, useState } from 'react'
import { ErrorApi, esRutaInexistente } from '../../api/cliente'

/** Solo enlaces http(s); evita que un dato mal capturado se vuelva un enlace peligroso. */
export function esEnlaceSeguro(url?: string | null): url is string {
  return !!url && /^https?:\/\//i.test(url)
}

export function mensajeDeError(error: unknown, accion: string): string {
  if (error instanceof ErrorApi) {
    if (esRutaInexistente(error)) return 'Esta función todavía no está disponible.'
    if (error.estado === 0) return 'No se pudo conectar con el servidor. Revisa tu conexión.'
    if (error.estado === 403) return `No tienes permiso para ${accion}.`
    if (error.estado === 404) return 'Esta iglesia no existe o ya no está disponible.'
    if (error.estado === 422 || error.estado === 400) return error.message
  }
  return `No se pudo ${accion}. Inténtalo otra vez.`
}

type Carga<T> =
  { tipo: 'cargando' } | { tipo: 'error'; mensaje: string } | { tipo: 'listo'; datos: T }

/** Pide datos al montar y permite reintentar. */
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
