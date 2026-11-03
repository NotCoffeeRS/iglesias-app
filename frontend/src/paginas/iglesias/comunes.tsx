import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

export function Cargando() {
  return (
    <div className="space-y-3" aria-hidden="true">
      {[0, 1].map((i) => (
        <div key={i} className="animate-pulse rounded-3xl border border-borde bg-superficie p-6">
          <div className="h-6 w-2/3 rounded-lg bg-superficie-2" />
          <div className="mt-3 h-4 w-1/2 rounded bg-superficie-2" />
        </div>
      ))}
    </div>
  )
}

export function ErrorConReintento({
  mensaje,
  reintentar,
}: {
  mensaje: string
  reintentar: () => void
}) {
  return (
    <div role="alert" className="rounded-3xl border border-borde bg-superficie p-6 text-center">
      <p className="font-semibold">{mensaje}</p>
      <button type="button" onClick={reintentar} className={claseBotonPrincipal + ' mt-4'}>
        Reintentar
      </button>
    </div>
  )
}

export function Volver({ a, children }: { a: string; children: ReactNode }) {
  return (
    <Link
      to={a}
      className="-ml-2 inline-flex items-center gap-1 rounded-xl px-2 py-1 text-sm font-semibold text-enlace hover:bg-superficie-2"
    >
      <svg
        viewBox="0 0 24 24"
        className="h-4 w-4"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        aria-hidden="true"
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 6l-6 6 6 6" />
      </svg>
      {children}
    </Link>
  )
}

export const claseBotonPrincipal =
  'inline-flex items-center justify-center rounded-xl bg-primario px-5 py-2.5 font-semibold text-sobre-primario transition-colors hover:bg-primario-hover disabled:cursor-not-allowed disabled:opacity-50'

export const claseBotonSecundario =
  'inline-flex items-center justify-center rounded-xl border border-borde bg-superficie px-5 py-2.5 font-semibold text-texto transition-colors hover:bg-superficie-2'

export const claseCampo =
  'mt-1.5 block w-full rounded-xl border border-borde bg-superficie-2 px-3.5 py-3 text-base text-texto ' +
  'transition-colors focus:border-enlace focus:bg-superficie focus:outline-none focus:ring-2 focus:ring-acento ' +
  'aria-invalid:border-peligro'
