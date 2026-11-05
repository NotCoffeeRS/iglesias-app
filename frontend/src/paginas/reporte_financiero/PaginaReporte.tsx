import { useState } from 'react'
import {
  listarIglesiasParaReporte,
  obtenerReporte,
  type Reporte,
  type Resumen,
  type ResumenIglesia,
} from '../../api/reporte_financiero'
import { Cargando, ErrorConReintento, SinAcceso } from './comunes'
import { Barras, Cifras } from './Graficas'
import {
  aCentavos,
  claseCampo,
  formatearMonto,
  hoyEnMerida,
  rangoDe,
  useCarga,
  type Periodo,
} from './utilidades'

const PERIODOS: { clave: Exclude<Periodo, 'otro'>; nombre: string }[] = [
  { clave: 'mes', nombre: 'Este mes' },
  { clave: 'mes_pasado', nombre: 'Mes pasado' },
  { clave: 'anio', nombre: 'Este año' },
]

function sinMovimientos(r: Resumen): boolean {
  return (
    (aCentavos(r.ingresos) ?? 0) === 0 &&
    (aCentavos(r.gastos) ?? 0) === 0 &&
    r.ingresos_por_tipo.length === 0 &&
    r.gastos_por_categoria.length === 0
  )
}

/** Detalle de un resumen: cifras y los dos desgloses. */
function Detalle({ resumen, titulo }: { resumen: Resumen; titulo: string }) {
  return (
    <div className="space-y-4">
      <Cifras resumen={resumen} titulo={titulo} />
      {sinMovimientos(resumen) ? (
        <p className="rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
          No hay movimientos en este periodo. Si ya se recaudó o se gastó algo, regístralo en
          Ingresos o en Gastos.
        </p>
      ) : (
        <>
          <Barras
            titulo="Ingresos por tipo"
            partidas={resumen.ingresos_por_tipo}
            vacio="No hubo ingresos en este periodo."
          />
          <Barras
            titulo="Gastos por categoría"
            partidas={resumen.gastos_por_categoria}
            vacio="No hubo gastos en este periodo."
          />
        </>
      )}
    </div>
  )
}

/** Una fila por iglesia; al tocarla se abre su detalle. */
function PorIglesia({
  iglesias,
  onElegir,
}: {
  iglesias: ResumenIglesia[]
  onElegir: (id: number) => void
}) {
  const ordenadas = [...iglesias].sort((a, b) =>
    a.iglesia_nombre.localeCompare(b.iglesia_nombre, 'es'),
  )
  return (
    <section>
      <h2 className="mb-2 px-1 text-lg font-semibold">Por iglesia</h2>
      <ul className="divide-y divide-borde overflow-hidden rounded-3xl border border-borde bg-superficie">
        {ordenadas.map((i) => {
          const balance = aCentavos(i.balance) ?? 0
          return (
            <li key={i.iglesia_id}>
              <button
                type="button"
                onClick={() => onElegir(i.iglesia_id)}
                aria-label={`Ver el detalle de ${i.iglesia_nombre}`}
                className="block w-full px-4 py-3.5 text-left transition-colors hover:bg-resalte"
              >
                <span className="flex items-baseline justify-between gap-3">
                  <span className="min-w-0 font-semibold">{i.iglesia_nombre}</span>
                  <span
                    className={
                      'shrink-0 font-semibold ' + (balance < 0 ? 'text-peligro' : 'text-texto')
                    }
                  >
                    {formatearMonto(balance)}
                  </span>
                </span>
                <span className="mt-1 grid grid-cols-2 gap-x-3 text-sm text-texto-suave">
                  <span>Ingresos {formatearMonto(aCentavos(i.ingresos) ?? 0)}</span>
                  <span>Gastos {formatearMonto(aCentavos(i.gastos) ?? 0)}</span>
                </span>
              </button>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

function Contenido({ reporte, onElegir }: { reporte: Reporte; onElegir: (id: number) => void }) {
  if (reporte.consolidado) {
    return (
      <div className="space-y-4">
        <Detalle resumen={reporte.consolidado} titulo="Balance de todo el Presbiterio" />
        {reporte.iglesias.length > 0 && (
          <PorIglesia iglesias={reporte.iglesias} onElegir={onElegir} />
        )}
      </div>
    )
  }
  if (reporte.iglesias.length === 1) {
    const unica = reporte.iglesias[0]
    return <Detalle resumen={unica} titulo={`Balance de ${unica.iglesia_nombre}`} />
  }
  if (reporte.iglesias.length > 1)
    return <PorIglesia iglesias={reporte.iglesias} onElegir={onElegir} />
  return (
    <p className="rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
      No hay iglesias a tu cargo para mostrar en el reporte.
    </p>
  )
}

export default function PaginaReporte() {
  const hoy = hoyEnMerida()
  const [periodo, setPeriodo] = useState<Periodo>('mes')
  const [rango, setRango] = useState(() => rangoDe('mes', hoy))
  const [iglesia, setIglesia] = useState('')

  const rangoValido = rango.desde !== '' && rango.hasta !== '' && rango.desde <= rango.hasta
  const clave = `${iglesia}|${rango.desde}|${rango.hasta}`

  const iglesias = useCarga(listarIglesiasParaReporte, 'cargar las iglesias', 'iglesias')
  const { estado, reintentar } = useCarga(
    () =>
      rangoValido
        ? obtenerReporte({ ...rango, iglesia_id: iglesia ? Number(iglesia) : undefined })
        : Promise.resolve(null),
    'cargar el reporte',
    clave,
  )

  const opcionesIglesia = iglesias.estado.tipo === 'listo' ? iglesias.estado.datos : []

  function elegirPeriodo(p: Exclude<Periodo, 'otro'>) {
    setPeriodo(p)
    setRango(rangoDe(p, hoy))
  }

  const claseChip = (activo: boolean) =>
    [
      'block rounded-full px-3.5 py-1.5 text-sm font-semibold whitespace-nowrap transition-colors',
      activo
        ? 'bg-primario text-sobre-primario'
        : 'border border-borde bg-superficie text-texto hover:bg-superficie-2',
    ].join(' ')

  return (
    <section>
      <h1 className="text-3xl font-bold md:text-4xl">Reporte financiero</h1>
      <p className="mt-1 text-texto-suave">
        Ingresos, gastos y balance por periodo. Lo anulado no cuenta.
      </p>

      {estado.tipo === 'error' && estado.sinAcceso ? (
        <div className="mt-5">
          <SinAcceso />
        </div>
      ) : (
        <>
          <nav
            aria-label="Periodo"
            className="-mx-4 mt-5 overflow-x-auto px-4 [scrollbar-width:none]"
          >
            <ul className="flex gap-2">
              {PERIODOS.map((p) => (
                <li key={p.clave}>
                  <button
                    type="button"
                    aria-pressed={periodo === p.clave}
                    onClick={() => elegirPeriodo(p.clave)}
                    className={claseChip(periodo === p.clave)}
                  >
                    {p.nombre}
                  </button>
                </li>
              ))}
            </ul>
          </nav>

          <div className="mt-3 grid grid-cols-2 gap-3 sm:max-w-lg">
            <label className="block text-sm font-semibold">
              Desde
              <input
                type="date"
                value={rango.desde}
                max={hoy}
                onChange={(e) => {
                  setPeriodo('otro')
                  setRango((r) => ({ ...r, desde: e.target.value }))
                }}
                className={claseCampo}
              />
            </label>
            <label className="block text-sm font-semibold">
              Hasta
              <input
                type="date"
                value={rango.hasta}
                max={hoy}
                onChange={(e) => {
                  setPeriodo('otro')
                  setRango((r) => ({ ...r, hasta: e.target.value }))
                }}
                className={claseCampo}
              />
            </label>
          </div>

          {opcionesIglesia.length > 1 && (
            <label className="mt-3 block max-w-md text-sm font-semibold">
              Iglesia
              <select
                value={iglesia}
                onChange={(e) => setIglesia(e.target.value)}
                className={claseCampo}
              >
                <option value="">Todas las iglesias</option>
                {opcionesIglesia.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.nombre}
                  </option>
                ))}
              </select>
            </label>
          )}

          <div className="mt-5">
            {!rangoValido && (
              <p role="alert" className="rounded-xl bg-peligro-fondo px-4 py-2.5 text-peligro">
                La fecha de inicio debe ser anterior o igual a la de fin.
              </p>
            )}
            {rangoValido && estado.tipo === 'cargando' && <Cargando />}
            {estado.tipo === 'error' && !estado.sinAcceso && (
              <ErrorConReintento mensaje={estado.mensaje} reintentar={reintentar} />
            )}
            {rangoValido && estado.tipo === 'listo' && estado.datos && (
              <div
                aria-busy={estado.actualizando}
                className={
                  estado.actualizando ? 'opacity-60 transition-opacity' : 'transition-opacity'
                }
              >
                {estado.actualizando && (
                  <p role="status" className="mb-3 text-sm text-texto-suave">
                    Actualizando…
                  </p>
                )}
                <Contenido reporte={estado.datos} onElegir={(id) => setIglesia(String(id))} />
              </div>
            )}
          </div>
        </>
      )}
    </section>
  )
}
