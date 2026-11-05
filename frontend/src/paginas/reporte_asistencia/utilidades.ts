import { useEffect, useState } from 'react'
import { ErrorApi } from '../../api/cliente'

type Estado<T> =
  { tipo: 'cargando' } | { tipo: 'error'; mensaje: string } | { tipo: 'listo'; datos: T }
export function useCarga<T>(pedir: () => Promise<T>, dependencia = '') {
  const [estado, setEstado] = useState<Estado<T>>({ tipo: 'cargando' })
  const [intento, setIntento] = useState(0)
  useEffect(() => {
    let vigente = true
    pedir()
      .then((datos) => {
        if (vigente) setEstado({ tipo: 'listo', datos })
      })
      .catch((e) => {
        if (!vigente) return
        const mensaje =
          e instanceof ErrorApi && e.estado === 403
            ? 'No tienes permiso para consultar ese reporte.'
            : e instanceof ErrorApi && e.estado === 422
              ? e.message
              : 'No se pudo cargar el reporte. Revisa tu conexión e inténtalo de nuevo.'
        setEstado({ tipo: 'error', mensaje })
      })
    return () => {
      vigente = false
    }
    // Recargar solo al aplicar filtros o pedir un reintento.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dependencia, intento])
  return {
    estado,
    reintentar: () => {
      setEstado({ tipo: 'cargando' })
      setIntento((n) => n + 1)
    },
  }
}
