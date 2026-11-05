import { BotonCerrarSesion } from '../../componentes/CuentaMenu'
import { nombreDelCargo, textoCargoEIglesia, useCuenta } from './cuenta'

export default function PaginaPerfil() {
  const cuenta = useCuenta()

  return (
    <section>
      <h1 className="text-3xl font-bold md:text-4xl">Mi perfil</h1>
      <p className="mt-1 text-texto-suave">La cuenta con la que estás usando la app.</p>

      {!cuenta ? (
        <div className="mt-5 h-40 animate-pulse rounded-3xl bg-superficie" aria-hidden="true" />
      ) : (
        <div className="mt-5 max-w-xl rounded-3xl border border-borde bg-superficie p-5">
          <div className="flex items-center gap-4">
            <span
              aria-hidden="true"
              className="grid h-14 w-14 shrink-0 place-items-center rounded-full bg-acento font-titulo text-2xl font-bold text-acento-texto"
            >
              {cuenta.yo.nombre_completo.trim().charAt(0).toUpperCase()}
            </span>
            <div className="min-w-0">
              <h2 className="truncate font-titulo text-xl font-semibold text-primario">
                {cuenta.yo.nombre_completo}
              </h2>
              <p className="text-texto-suave">{textoCargoEIglesia(cuenta)}</p>
            </div>
          </div>

          <dl className="mt-5 grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
            <dt className="text-texto-suave">Cargo</dt>
            <dd className="font-semibold">{nombreDelCargo(cuenta.yo.cargo)}</dd>
            <dt className="text-texto-suave">Iglesia</dt>
            <dd className="font-semibold">
              {cuenta.yo.iglesia_id === null ? 'Todas las iglesias' : (cuenta.iglesia ?? '—')}
            </dd>
          </dl>

          <div className="mt-6 max-w-xs">
            <BotonCerrarSesion />
          </div>
        </div>
      )}
    </section>
  )
}
