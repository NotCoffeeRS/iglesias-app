import { useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  anularGasto,
  CATEGORIAS,
  listarGastos,
  listarIglesiasParaGastos,
  type Gasto,
} from '../../api/gastos'
import { Cargando, ErrorConReintento, SinAcceso } from './comunes'
import {
  aCentavos,
  claseBotonPrincipal,
  claseBotonSecundario,
  claseCampo,
  fechaLarga,
  formatearMonto,
  hoyEnMerida,
  mensajeDeError,
  nombreCategoria,
  rangoDe,
  useCarga,
  type Periodo,
} from './utilidades'

const PERIODOS: { clave: Exclude<Periodo, 'otro'>; nombre: string }[] = [
  { clave: 'mes', nombre: 'Este mes' },
  { clave: 'mes_pasado', nombre: 'Mes pasado' },
  { clave: 'anio', nombre: 'Este año' },
]

const centavosDe = (g: Gasto) => aCentavos(g.monto) ?? 0

function Resumen({ gastos }: { gastos: Gasto[] }) {
  const vigentes = gastos.filter((g) => !g.anulado)
  const anulados = gastos.length - vigentes.length
  const total = vigentes.reduce((suma, g) => suma + centavosDe(g), 0)
  const porCategoria = CATEGORIAS.map((c) => ({
    ...c,
    centavos: vigentes
      .filter((g) => g.categoria === c.clave)
      .reduce((s, g) => s + centavosDe(g), 0),
  })).filter((c) => c.centavos > 0)

  return (
    <section
      aria-label="Resumen del periodo"
      className="rounded-3xl border border-borde bg-superficie p-5"
    >
      <p className="text-sm text-texto-suave">Total de gastos</p>
      <p className="font-titulo text-4xl font-bold text-primario tabular-nums">
        {formatearMonto(total)}
      </p>
      {porCategoria.length > 0 && (
        <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          {porCategoria.map((c) => (
            <div key={c.clave}>
              <dt className="text-texto-suave">{c.nombre}</dt>
              <dd className="font-semibold tabular-nums">{formatearMonto(c.centavos)}</dd>
            </div>
          ))}
        </dl>
      )}
      {anulados > 0 && (
        <p className="mt-4 text-sm text-texto-suave">
          {anulados === 1
            ? '1 gasto anulado no cuenta.'
            : `${anulados} gastos anulados no cuentan.`}
        </p>
      )}
    </section>
  )
}

function Fila({
  gasto,
  mostrarIglesia,
  onAnulado,
}: {
  gasto: Gasto
  mostrarIglesia: boolean
  onAnulado: (g: Gasto) => void
}) {
  const [anulando, setAnulando] = useState(false)
  const [motivo, setMotivo] = useState('')
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function confirmar() {
    if (!motivo.trim()) {
      setError('Escribe el motivo de la anulación.')
      return
    }
    setGuardando(true)
    setError(null)
    try {
      onAnulado(await anularGasto(gasto.id, motivo.trim()))
      setAnulando(false)
    } catch (e) {
      setError(mensajeDeError(e, 'anular este gasto'))
    } finally {
      setGuardando(false)
    }
  }

  return (
    <li className="px-4 py-3.5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className={'font-semibold ' + (gasto.anulado ? 'text-texto-suave line-through' : '')}>
            {nombreCategoria(gasto.categoria)}
            {gasto.anulado && (
              <span className="ml-2 rounded-full border border-borde px-2 py-0.5 align-middle text-xs font-semibold no-underline">
                Anulado
              </span>
            )}
          </p>
          {gasto.nota && <p className="text-sm text-texto-suave">{gasto.nota}</p>}
          {mostrarIglesia && gasto.iglesia_nombre && (
            <p className="text-sm text-texto-suave">{gasto.iglesia_nombre}</p>
          )}
          {gasto.anulado && gasto.motivo_anulacion && (
            <p className="mt-1 text-sm text-texto-suave">Motivo: {gasto.motivo_anulacion}</p>
          )}
        </div>
        <p
          className={
            'shrink-0 font-semibold tabular-nums ' +
            (gasto.anulado ? 'text-texto-suave line-through' : '')
          }
        >
          {formatearMonto(centavosDe(gasto))}
        </p>
      </div>

      {!gasto.anulado && !anulando && (
        <button
          type="button"
          onClick={() => setAnulando(true)}
          className="mt-1 -ml-2.5 rounded-lg px-2.5 py-1.5 text-sm font-semibold text-peligro hover:bg-peligro-fondo"
        >
          Anular
        </button>
      )}

      {anulando && (
        <div className="mt-3 space-y-3 rounded-2xl bg-superficie-2 p-4">
          <label className="block text-sm font-semibold">
            Motivo de la anulación
            <textarea
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              rows={2}
              aria-invalid={error ? true : undefined}
              className={claseCampo}
            />
          </label>
          <p className="text-sm text-texto-suave">
            El gasto no se borra: queda anulado con este motivo y deja de contar en los totales.
          </p>
          {error && (
            <p role="alert" className="text-sm text-peligro">
              {error}
            </p>
          )}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={confirmar}
              disabled={guardando}
              className="inline-flex items-center justify-center rounded-xl bg-peligro px-4 py-2.5 font-semibold text-superficie transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {guardando ? 'Anulando…' : 'Anular gasto'}
            </button>
            <button
              type="button"
              onClick={() => {
                setAnulando(false)
                setError(null)
              }}
              className={claseBotonSecundario}
            >
              Cancelar
            </button>
          </div>
        </div>
      )}
    </li>
  )
}

export default function PaginaGastos() {
  const hoy = hoyEnMerida()
  const aviso = (useLocation().state as { aviso?: string } | null)?.aviso
  const [periodo, setPeriodo] = useState<Periodo>('mes')
  const [rango, setRango] = useState(() => rangoDe('mes', hoy))
  const [iglesia, setIglesia] = useState('')
  // Gastos anulados en esta visita, para mostrarlos al instante sin volver a pedir la lista.
  const [anulados, setAnulados] = useState<Record<number, Gasto>>({})

  const rangoValido = rango.desde !== '' && rango.hasta !== '' && rango.desde <= rango.hasta
  const clave = `${iglesia}|${rango.desde}|${rango.hasta}`

  const iglesias = useCarga(listarIglesiasParaGastos, 'cargar las iglesias', 'iglesias')
  const { estado, reintentar } = useCarga(
    () =>
      rangoValido
        ? listarGastos({ ...rango, iglesia_id: iglesia ? Number(iglesia) : undefined })
        : Promise.resolve([] as Gasto[]),
    'cargar los gastos',
    clave,
  )

  const opcionesIglesia = iglesias.estado.tipo === 'listo' ? iglesias.estado.datos : []

  const gastos = useMemo(() => {
    if (estado.tipo !== 'listo') return []
    return estado.datos
      .map((g) => anulados[g.id] ?? g)
      .sort((a, b) => b.fecha.localeCompare(a.fecha) || b.id - a.id)
  }, [estado, anulados])

  const porFecha = useMemo(() => {
    const grupos: { fecha: string; items: Gasto[] }[] = []
    for (const g of gastos) {
      const ultimo = grupos[grupos.length - 1]
      if (ultimo && ultimo.fecha === g.fecha) ultimo.items.push(g)
      else grupos.push({ fecha: g.fecha, items: [g] })
    }
    return grupos
  }, [gastos])

  function elegirPeriodo(p: Exclude<Periodo, 'otro'>) {
    setPeriodo(p)
    setRango(rangoDe(p, hoy))
  }

  const claseChip = (activo: boolean) =>
    [
      'block rounded-full px-3.5 py-1.5 text-sm font-semibold whitespace-nowrap transition-colors',
      activo
        ? 'bg-primario text-sobre-primario'
        : 'border border-borde bg-superficie text-texto hover:bg-resalte',
    ].join(' ')

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold md:text-4xl">Gastos</h1>
          <p className="mt-1 text-texto-suave">Luz, agua, renta, mantenimiento y demás gastos.</p>
        </div>
        <Link to="/gastos/nuevo" className={claseBotonPrincipal}>
          Registrar gasto
        </Link>
      </div>

      {aviso && (
        <p
          role="status"
          className="mt-4 rounded-xl bg-acento px-4 py-2.5 font-semibold text-acento-texto"
        >
          {aviso}
        </p>
      )}

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

          <div className="mt-5 space-y-5">
            {!rangoValido && (
              <p role="alert" className="rounded-xl bg-peligro-fondo px-4 py-2.5 text-peligro">
                La fecha de inicio debe ser anterior o igual a la de fin.
              </p>
            )}
            {rangoValido && estado.tipo === 'cargando' && <Cargando />}
            {estado.tipo === 'error' && !estado.sinAcceso && (
              <ErrorConReintento mensaje={estado.mensaje} reintentar={reintentar} />
            )}
            {rangoValido && estado.tipo === 'listo' && (
              <>
                <Resumen gastos={gastos} />
                {gastos.length === 0 ? (
                  <p className="rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
                    No hay gastos en este periodo. Si ya se pagó algo, regístralo.
                  </p>
                ) : (
                  porFecha.map((g) => (
                    <div key={g.fecha}>
                      <h2 className="mb-2 px-1 text-base font-semibold first-letter:uppercase">
                        {fechaLarga(g.fecha)}
                      </h2>
                      <ul className="divide-y divide-borde overflow-hidden rounded-3xl border border-borde bg-superficie">
                        {g.items.map((item) => (
                          <Fila
                            key={item.id}
                            gasto={item}
                            mostrarIglesia={!iglesia && opcionesIglesia.length > 1}
                            onAnulado={(actualizado) =>
                              setAnulados((a) => ({ ...a, [actualizado.id]: actualizado }))
                            }
                          />
                        ))}
                      </ul>
                    </div>
                  ))
                )}
              </>
            )}
          </div>
        </>
      )}
    </section>
  )
}
