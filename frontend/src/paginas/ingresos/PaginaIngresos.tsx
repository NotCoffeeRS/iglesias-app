import { useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  anularIngreso,
  listarIglesiasParaIngresos,
  listarIngresos,
  TIPOS,
  type Ingreso,
} from '../../api/ingresos'
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
  nombreCulto,
  nombreTipo,
  rangoDe,
  useCarga,
  type Periodo,
} from './utilidades'

const PERIODOS: { clave: Exclude<Periodo, 'otro'>; nombre: string }[] = [
  { clave: 'mes', nombre: 'Este mes' },
  { clave: 'mes_pasado', nombre: 'Mes pasado' },
  { clave: 'anio', nombre: 'Este año' },
]

const centavosDe = (i: Ingreso) => aCentavos(i.monto) ?? 0

function Resumen({ ingresos }: { ingresos: Ingreso[] }) {
  const vigentes = ingresos.filter((i) => !i.anulado)
  const anulados = ingresos.length - vigentes.length
  const total = vigentes.reduce((suma, i) => suma + centavosDe(i), 0)
  const porTipo = TIPOS.map((t) => ({
    ...t,
    centavos: vigentes.filter((i) => i.tipo === t.clave).reduce((s, i) => s + centavosDe(i), 0),
  })).filter((t) => t.centavos > 0)

  return (
    <section
      aria-label="Resumen del periodo"
      className="rounded-3xl bg-primario p-5 text-sobre-primario"
    >
      <p className="text-sm opacity-85">Total de ingresos</p>
      <p className="font-titulo text-4xl font-bold tabular-nums">{formatearMonto(total)}</p>
      {porTipo.length > 0 && (
        <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          {porTipo.map((t) => (
            <div key={t.clave}>
              <dt className="opacity-85">{t.nombre}</dt>
              <dd className="font-semibold tabular-nums">{formatearMonto(t.centavos)}</dd>
            </div>
          ))}
        </dl>
      )}
      {anulados > 0 && (
        <p className="mt-4 text-sm opacity-85">
          {anulados === 1
            ? '1 ingreso anulado no cuenta.'
            : `${anulados} ingresos anulados no cuentan.`}
        </p>
      )}
    </section>
  )
}

function Fila({
  ingreso,
  mostrarIglesia,
  onAnulado,
}: {
  ingreso: Ingreso
  mostrarIglesia: boolean
  onAnulado: (i: Ingreso) => void
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
      onAnulado(await anularIngreso(ingreso.id, motivo.trim()))
      setAnulando(false)
    } catch (e) {
      setError(mensajeDeError(e, 'anular este ingreso'))
    } finally {
      setGuardando(false)
    }
  }

  const detalle = [nombreCulto(ingreso.culto), mostrarIglesia ? ingreso.iglesia_nombre : null]
    .filter(Boolean)
    .join(' · ')

  return (
    <li className="px-4 py-3.5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p
            className={'font-semibold ' + (ingreso.anulado ? 'text-texto-suave line-through' : '')}
          >
            {nombreTipo(ingreso.tipo)}
            {ingreso.anulado && (
              <span className="ml-2 rounded-full border border-borde px-2 py-0.5 align-middle text-xs font-semibold no-underline">
                Anulado
              </span>
            )}
          </p>
          {ingreso.descripcion && <p className="text-sm text-texto-suave">{ingreso.descripcion}</p>}
          {detalle && <p className="text-sm text-texto-suave">{detalle}</p>}
          {ingreso.anulado && ingreso.motivo_anulacion && (
            <p className="mt-1 text-sm text-texto-suave">Motivo: {ingreso.motivo_anulacion}</p>
          )}
        </div>
        <p
          className={
            'shrink-0 font-semibold tabular-nums ' +
            (ingreso.anulado ? 'text-texto-suave line-through' : '')
          }
        >
          {formatearMonto(centavosDe(ingreso))}
        </p>
      </div>

      {!ingreso.anulado && !anulando && (
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
            El ingreso no se borra: queda anulado con este motivo y deja de contar en los totales.
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
              {guardando ? 'Anulando…' : 'Anular ingreso'}
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

export default function PaginaIngresos() {
  const hoy = hoyEnMerida()
  const aviso = (useLocation().state as { aviso?: string } | null)?.aviso
  const [periodo, setPeriodo] = useState<Periodo>('mes')
  const [rango, setRango] = useState(() => rangoDe('mes', hoy))
  const [iglesia, setIglesia] = useState('')
  // Ingresos anulados en esta visita, para mostrarlos al instante sin volver a pedir la lista.
  const [anulados, setAnulados] = useState<Record<number, Ingreso>>({})

  const rangoValido = rango.desde !== '' && rango.hasta !== '' && rango.desde <= rango.hasta
  const clave = `${iglesia}|${rango.desde}|${rango.hasta}`

  const iglesias = useCarga(listarIglesiasParaIngresos, 'cargar las iglesias', 'iglesias')
  const { estado, reintentar } = useCarga(
    () =>
      rangoValido
        ? listarIngresos({ ...rango, iglesia_id: iglesia ? Number(iglesia) : undefined })
        : Promise.resolve([] as Ingreso[]),
    'cargar los ingresos',
    clave,
  )

  const opcionesIglesia = iglesias.estado.tipo === 'listo' ? iglesias.estado.datos : []

  const ingresos = useMemo(() => {
    if (estado.tipo !== 'listo') return []
    return estado.datos
      .map((i) => anulados[i.id] ?? i)
      .sort((a, b) => b.fecha.localeCompare(a.fecha) || b.id - a.id)
  }, [estado, anulados])

  const porFecha = useMemo(() => {
    const grupos: { fecha: string; items: Ingreso[] }[] = []
    for (const i of ingresos) {
      const ultimo = grupos[grupos.length - 1]
      if (ultimo && ultimo.fecha === i.fecha) ultimo.items.push(i)
      else grupos.push({ fecha: i.fecha, items: [i] })
    }
    return grupos
  }, [ingresos])

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
          <h1 className="text-3xl font-bold md:text-4xl">Ingresos</h1>
          <p className="mt-1 text-texto-suave">Diezmos, ofrendas y demás lo recaudado por culto.</p>
        </div>
        <Link to="/ingresos/nuevo" className={claseBotonPrincipal}>
          Registrar ingresos
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
                <Resumen ingresos={ingresos} />
                {ingresos.length === 0 ? (
                  <p className="rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
                    No hay ingresos en este periodo. Si ya se recaudó algo, regístralo.
                  </p>
                ) : (
                  porFecha.map((g) => (
                    <div key={g.fecha}>
                      <h2 className="mb-2 px-1 text-base font-semibold first-letter:uppercase">
                        {fechaLarga(g.fecha)}
                      </h2>
                      <ul className="divide-y divide-borde overflow-hidden rounded-3xl border border-borde bg-superficie">
                        {g.items.map((i) => (
                          <Fila
                            key={i.id}
                            ingreso={i}
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
