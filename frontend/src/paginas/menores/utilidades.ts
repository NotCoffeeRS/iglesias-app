import { useEffect, useState } from 'react'
import { ErrorApi } from '../../api/cliente'
import type { Categoria } from '../../api/menores'

export const CATEGORIAS: Record<Categoria, string> = {
  nino: 'Niño',
  nina: 'Niña',
  adolescente: 'Adolescente',
}
export const esGestor = (cargo: string) => ['presbitero', 'pastor', 'apoyo_pastor'].includes(cargo)
export function mensaje(error: unknown): string {
  if (error instanceof ErrorApi) {
    if (error.estado === 403) return 'No tienes permiso para consultar o gestionar estos registros.'
    if (error.estado === 404) return 'El registro no existe o no está en tu alcance.'
    if (error.estado === 422 || error.estado === 409) return error.message
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
    // Solo recargar al cambiar el registro o al pedir un reintento.
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
