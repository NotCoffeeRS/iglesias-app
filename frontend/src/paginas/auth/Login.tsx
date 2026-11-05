import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { haySesion, iniciarSesion } from '../../api/auth'
import { ErrorApi } from '../../api/cliente'
import Logo from '../../componentes/Logo'
import LogoIafcj from '../../componentes/LogoIafcj'

function mensajeDeError(error: unknown): string {
  if (error instanceof ErrorApi) {
    if (error.estado === 401) return 'Usuario o contraseña incorrectos.'
    if (error.estado === 0) return 'No se pudo conectar con el servidor. Revisa tu conexión.'
  }
  return 'No se pudo iniciar sesión. Intenta de nuevo.'
}

const claseCampo =
  'mt-1.5 block w-full rounded-xl border border-borde bg-superficie-2 px-3.5 py-3 text-base text-texto ' +
  'transition-colors focus:border-enlace focus:bg-superficie focus:outline-none focus:ring-2 focus:ring-acento'

export default function Login() {
  const navegar = useNavigate()
  const ubicacion = useLocation()
  const destino = (ubicacion.state as { desde?: string } | null)?.desde ?? '/'

  const [usuario, setUsuario] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [verContrasena, setVerContrasena] = useState(false)
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
        <div className="mb-8">
          <h1>
            <Logo tipo="completo" alt="Tessia" className="mx-auto h-44 w-auto sm:h-52" />
          </h1>
          <p className="mt-1 text-center text-texto-suave">Presbiterio de la 3ra IAFCJ</p>
        </div>

        <form
          onSubmit={enviar}
          className="rounded-3xl border border-borde bg-superficie p-6 shadow-sm"
          noValidate
        >
          <h2 className="text-xl font-semibold">Iniciar sesión</h2>

          {error && (
            <p
              role="alert"
              className="mt-4 rounded-xl bg-peligro-fondo px-3.5 py-2.5 text-sm text-peligro"
            >
              {error}
            </p>
          )}

          <label className="mt-5 block text-sm font-semibold text-texto">
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

          <div className="mt-4">
            <label htmlFor="contrasena" className="block text-sm font-semibold text-texto">
              Contraseña
            </label>
            <div className="relative">
              <input
                id="contrasena"
                type={verContrasena ? 'text' : 'password'}
                name="contrasena"
                autoComplete="current-password"
                required
                value={contrasena}
                onChange={(e) => setContrasena(e.target.value)}
                className={claseCampo + ' pr-12'}
              />
              <button
                type="button"
                onClick={() => setVerContrasena((v) => !v)}
                aria-label={verContrasena ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                aria-pressed={verContrasena}
                className="absolute inset-y-0 right-1 mt-1.5 grid w-11 place-items-center rounded-xl text-texto-suave transition-colors hover:text-texto focus:outline-none focus-visible:ring-2 focus-visible:ring-acento"
              >
                <svg
                  viewBox="0 0 24 24"
                  className="h-5 w-5"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" />
                  <circle cx="12" cy="12" r="3" />
                  {verContrasena && <path d="M4 4l16 16" />}
                </svg>
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={enviando || !usuario.trim() || !contrasena}
            className="mt-6 w-full rounded-xl bg-primario px-4 py-3 text-base font-semibold text-sobre-primario transition-colors hover:bg-primario-hover disabled:cursor-not-allowed disabled:opacity-50"
          >
            {enviando ? 'Entrando…' : 'Entrar'}
          </button>
        </form>

        <div className="mt-8 flex justify-center">
          <LogoIafcj className="h-24 w-auto" />
        </div>
      </div>
    </main>
  )
}
