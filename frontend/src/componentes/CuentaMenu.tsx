import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { cerrarSesion } from '../api/auth'
import { textoCargoEIglesia, useCuenta } from '../paginas/auth/cuenta'

/** Cerrar sesión pide confirmación: no se cierra con un solo toque. */
export function BotonCerrarSesion({ alCerrar }: { alCerrar?: () => void }) {
  const navegar = useNavigate()
  const [confirmando, setConfirmando] = useState(false)

  function cerrar() {
    cerrarSesion()
    alCerrar?.()
    navegar('/login', { replace: true })
  }

  if (!confirmando) {
    return (
      <button
        type="button"
        onClick={() => setConfirmando(true)}
        className="w-full rounded-xl border border-borde px-3.5 py-2.5 text-center font-semibold text-peligro transition-colors hover:bg-peligro-fondo"
      >
        Cerrar sesión
      </button>
    )
  }

  return (
    <div
      role="alertdialog"
      aria-label="Confirmar cierre de sesión"
      onKeyDown={(e) => e.key === 'Escape' && setConfirmando(false)}
      className="rounded-xl border border-peligro/40 bg-peligro-fondo p-3"
    >
      <p className="text-center text-sm font-semibold text-peligro">¿Cerrar sesión?</p>
      <div className="mt-2 flex gap-2">
        <button
          type="button"
          autoFocus
          onClick={() => setConfirmando(false)}
          className="flex-1 rounded-lg border border-borde bg-superficie px-3 py-2 text-sm font-semibold text-texto"
        >
          Cancelar
        </button>
        <button
          type="button"
          onClick={cerrar}
          className="flex-1 rounded-lg bg-primario px-3 py-2 text-sm font-semibold text-sobre-primario hover:bg-primario-hover"
        >
          Sí, cerrar
        </button>
      </div>
    </div>
  )
}

/** Bloque al pie del menú: con qué cuenta se está, acceso al perfil y cerrar sesión. */
export default function CuentaMenu({ alNavegar }: { alNavegar?: () => void }) {
  const cuenta = useCuenta()
  const nombre = cuenta?.yo.nombre_completo ?? ''
  const inicial = nombre.trim().charAt(0).toUpperCase()

  return (
    <section aria-label="Mi cuenta" className="mt-auto border-t border-borde px-3 py-4">
      <Link
        to="/perfil"
        onClick={alNavegar}
        className="flex items-center gap-3 rounded-xl px-2 py-2 transition-colors hover:bg-superficie-2"
      >
        <span
          aria-hidden="true"
          className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-acento font-titulo text-lg font-bold text-acento-texto"
        >
          {inicial || '·'}
        </span>
        <span className="min-w-0">
          <span className="line-clamp-2 font-semibold leading-snug">{nombre || 'Mi cuenta'}</span>
          <span className="line-clamp-2 text-sm leading-snug text-texto-suave">
            {cuenta ? textoCargoEIglesia(cuenta) : 'Ver mi perfil'}
          </span>
        </span>
      </Link>
      <div className="mt-3">
        <BotonCerrarSesion alCerrar={alNavegar} />
      </div>
    </section>
  )
}
