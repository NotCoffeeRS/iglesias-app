import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { EstadoMiembro } from '../../api/miembros'
import { claseBotonPrincipal, nombreEstado } from './utilidades'

export function Cargando() {
  return (
    <div className="space-y-2" aria-hidden="true">
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className="h-[4.25rem] animate-pulse rounded-2xl bg-superficie" />
      ))}
    </div>
  )
}

export function ErrorConReintento({
  mensaje,
  reintentar,
}: {
  mensaje: string
  reintentar?: () => void
}) {
  return (
    <div role="alert" className="rounded-3xl border border-borde bg-superficie p-6 text-center">
      <p className="font-semibold">{mensaje}</p>
      {reintentar && (
        <button type="button" onClick={reintentar} className={claseBotonPrincipal + ' mt-4'}>
          Reintentar
        </button>
      )}
    </div>
  )
}

const ESTILO_ESTADO: Record<EstadoMiembro, string> = {
  activo: 'bg-acento text-acento-texto',
  visitante: 'border border-enlace text-enlace',
  en_proceso_ganar: 'bg-superficie-2 text-texto',
  en_proceso_consolidar: 'bg-superficie-2 text-texto',
  en_proceso_discipular: 'bg-superficie-2 text-texto',
  inactivo: 'text-texto-suave border border-borde',
}

export function EtiquetaEstado({ estado }: { estado: EstadoMiembro }) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap ${ESTILO_ESTADO[estado] ?? ''}`}
    >
      {nombreEstado(estado)}
    </span>
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
