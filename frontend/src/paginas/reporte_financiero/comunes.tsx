import { claseBotonPrincipal } from './utilidades'

export function Cargando() {
  return (
    <div className="space-y-4" aria-hidden="true">
      <div className="h-56 animate-pulse rounded-3xl bg-superficie" />
      <div className="h-40 animate-pulse rounded-3xl bg-superficie" />
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

/** Cuando el servidor niega el acceso al dinero (D9). */
export function SinAcceso() {
  return (
    <p className="rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
      Tu cargo no tiene acceso al reporte financiero. Solo lo ven el pastor y el tesorero de cada
      iglesia, y el presbítero.
    </p>
  )
}
