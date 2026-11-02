import { useEffect, useState, type ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { haySesion } from '../../api/auth'
import { EVENTO_SESION_EXPIRADA } from '../../api/cliente'

/** Envuelve las rutas privadas: sin sesión (o si la API la da por vencida) manda al login. */
export default function RequiereSesion({ children }: { children: ReactNode }) {
  const ubicacion = useLocation()
  const [, setVersion] = useState(0)

  useEffect(() => {
    const alExpirar = () => setVersion((v) => v + 1)
    window.addEventListener(EVENTO_SESION_EXPIRADA, alExpirar)
    return () => window.removeEventListener(EVENTO_SESION_EXPIRADA, alExpirar)
  }, [])

  if (!haySesion()) {
    return <Navigate to="/login" replace state={{ desde: ubicacion.pathname }} />
  }
  return children
}
