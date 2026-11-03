import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { cerrarSesion } from '../../api/auth'

export default function CerrarSesion() {
  const navegar = useNavigate()

  useEffect(() => {
    cerrarSesion()
    navegar('/login', { replace: true })
  }, [navegar])

  return null
}
