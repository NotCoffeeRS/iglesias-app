import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { haySesion, iniciarSesion } from '../../api/auth'
import { ErrorApi } from '../../api/cliente'

function mensajeDeError(error: unknown): string {
  if (error instanceof ErrorApi) {
    if (error.estado === 401) return 'Usuario o contraseña incorrectos.'
    if (error.estado === 0) return 'No se pudo conectar con el servidor. Revisa tu conexión.'
  }
  return 'No se pudo iniciar sesión. Intenta de nuevo.'
}

const claseCampo =
  'mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-base ' +
  'focus:border-primario focus:outline-none focus:ring-2 focus:ring-acento'

export default function Login() {
  const navegar = useNavigate()
  const ubicacion = useLocation()
  const destino = (ubicacion.state as { desde?: string } | null)?.desde ?? '/'

  const [usuario, setUsuario] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  if (haySesion()) return <Navigate to={destino} replace />

  async function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      await iniciarSesion(usuario.trim(), contrasena)
      navegar(destino, { replace: true })
    } catch (e) {
      setError(mensajeDeError(e))
      setEnviando(false)
    }
  }

  return (
    <main className="flex min-h-dvh items-center justify-center bg-fondo px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold text-primario">Iglesias App</h1>
          <p className="mt-1 text-slate-600">Presbiterio de la 3ra IAFCJ</p>
        </div>

        <form onSubmit={enviar} className="rounded-2xl bg-white p-6 shadow-sm" noValidate>
          <h2 className="text-lg font-semibold text-slate-800">Iniciar sesión</h2>

          {error && (
            <p
              role="alert"
              className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
            >
              {error}
            </p>
          )}

          <label className="mt-4 block text-sm font-medium text-slate-700">
            Usuario
            <input
              type="text"
              name="usuario"
              autoComplete="username"
              autoCapitalize="none"
              autoCorrect="off"
              required
              value={usuario}
              onChange={(e) => setUsuario(e.target.value)}
              className={claseCampo}
            />
          </label>

          <label className="mt-4 block text-sm font-medium text-slate-700">
            Contraseña
            <input
              type="password"
              name="contrasena"
              autoComplete="current-password"
              required
              value={contrasena}
              onChange={(e) => setContrasena(e.target.value)}
              className={claseCampo}
            />
          </label>

          <button
            type="submit"
            disabled={enviando || !usuario.trim() || !contrasena}
            className="mt-6 w-full rounded-lg bg-primario px-4 py-3 text-base font-semibold text-white hover:bg-primario-claro disabled:cursor-not-allowed disabled:opacity-60"
          >
            {enviando ? 'Entrando…' : 'Entrar'}
          </button>
        </form>
      </div>
    </main>
  )
}
