import { useEffect, useState } from 'react'
import { ErrorApi } from '../../api/cliente'

export function mensaje(error: unknown): string {
  if (error instanceof ErrorApi) {
    if (error.estado === 403) return 'No tienes permiso para realizar esta acción en este grupo.'
    if (error.estado === 404) return 'El grupo o la asignación ya no existe. Recarga la pantalla.'
    if (error.estado === 409 || error.estado === 422) return error.message
    if (error.estado === 0) return 'No se pudo conectar con la API. Revisa que esté encendida.'
  }
  return 'No se pudo completar la operación. Inténtalo otra vez.'
}
type Estado<T> =
  { tipo: 'cargando' } | { tipo: 'error'; mensaje: string } | { tipo: 'listo'; datos: T }
export function useCarga<T>(pedir: () => Promise<T>, dependencia?: unknown) {
  const [estado, setEstado] = useState<Estado<T>>({ tipo: 'cargando' })
  const [intento, setIntento] = useState(0)
  useEffect(() => {
    let vigente = true
    pedir()
      .then((datos) => {
        if (vigente) setEstado({ tipo: 'listo', datos })
      })
      .catch((error) => {
        if (vigente) setEstado({ tipo: 'error', mensaje: mensaje(error) })
      })
    return () => {
      vigente = false
    }
    // Volver a pedir solo al cambiar el grupo o después de una operación/reintento.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intento, dependencia])
  return {
    estado,
    reintentar: () => {
      setEstado({ tipo: 'cargando' })
      setIntento((n) => n + 1)
    },
  }
}
