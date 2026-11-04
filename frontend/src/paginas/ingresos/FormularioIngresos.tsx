import { useState, type FormEvent, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  CULTOS,
  listarIglesiasParaIngresos,
  registrarIngresos,
  TIPOS,
  type Culto,
  type IglesiaOpcion,
  type Partida,
  type TipoIngreso,
} from '../../api/ingresos'
import { Cargando, ErrorConReintento, SinAcceso, Volver } from './comunes'
import {
  aTextoMonto,
  claseBotonPrincipal,
  claseBotonSecundario,
  claseCampo,
  formatearMonto,
  hoyEnMerida,
  leerMonto,
  mensajeDeError,
  useCarga,
} from './utilidades'

type Montos = Record<TipoIngreso, string>
type Errores = Partial<
  Record<TipoIngreso | 'iglesia' | 'fecha' | 'descripcion' | 'general', string>
>

const MONTOS_VACIOS: Montos = { diezmos: '', ofrendas: '', evami: '', talento: '', otras: '' }

function Campo({
  etiqueta,
  error,
  ayuda,
  children,
}: {
  etiqueta: string
  error?: string
  ayuda?: string
  children: ReactNode
}) {
  return (
    <label className="block text-sm font-semibold">
      {etiqueta}
      {children}
      {error ? (
        <span className="mt-1 block font-normal text-peligro">{error}</span>
      ) : (
        ayuda && <span className="mt-1 block font-normal text-texto-suave">{ayuda}</span>
      )}
    </label>
  )
}

function Editor({ iglesias }: { iglesias: IglesiaOpcion[] }) {
  const navegar = useNavigate()
  const hoy = hoyEnMerida()
  const [iglesia, setIglesia] = useState(iglesias.length === 1 ? String(iglesias[0].id) : '')
  const [fecha, setFecha] = useState(hoy)
  const [culto, setCulto] = useState<Culto | ''>('')
  const [montos, setMontos] = useState<Montos>(MONTOS_VACIOS)
  const [descripcion, setDescripcion] = useState('')
  const [errores, setErrores] = useState<Errores>({})
  const [guardando, setGuardando] = useState(false)

  // Total en vivo: solo suma lo que ya es un monto válido.
  const total = TIPOS.reduce((suma, t) => suma + (leerMonto(montos[t.clave]) ?? 0), 0)

  function validar(): Errores {
    const e: Errores = {}
    if (!iglesia) e.iglesia = 'Elige la iglesia.'
    if (!fecha) e.fecha = 'Indica la fecha.'
    else if (fecha > hoy) e.fecha = 'No puede ser una fecha futura.'
    let capturados = 0
    for (const t of TIPOS) {
      const texto = montos[t.clave].trim()
      if (!texto) continue
      capturados++
      const centavos = leerMonto(texto)
      if (centavos === null) e[t.clave] = 'Escribe un monto válido, como 1500 o 1500.50.'
      else if (centavos <= 0) e[t.clave] = 'El monto debe ser mayor a 0.'
    }
    if (capturados === 0) e.general = 'Captura al menos un monto.'
    if (montos.otras.trim() && !descripcion.trim())
      e.descripcion = 'Describe de qué fueron las otras donaciones.'
    return e
  }

  async function guardar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const encontrados = validar()
    setErrores(encontrados)
    if (Object.keys(encontrados).length > 0) return

    const partidas: Partida[] = TIPOS.filter((t) => montos[t.clave].trim()).map((t) => ({
      tipo: t.clave,
      monto: aTextoMonto(leerMonto(montos[t.clave]) as number),
      descripcion: t.clave === 'otras' ? descripcion.trim() : null,
    }))
    setGuardando(true)
    try {
      await registrarIngresos({
        iglesia_id: Number(iglesia),
        fecha,
        culto: culto || null,
        partidas,
      })
      navegar('/ingresos', {
        replace: true,
        state: { aviso: `Ingresos registrados: ${formatearMonto(total)}.` },
      })
    } catch (e) {
      setErrores({ general: mensajeDeError(e, 'registrar ingresos en esta iglesia') })
      setGuardando(false)
    }
  }

  return (
    <form onSubmit={guardar} noValidate className="mt-3 space-y-5">
      <h1 className="text-3xl font-bold">Registrar ingresos</h1>

      {errores.general && (
        <p role="alert" className="rounded-xl bg-peligro-fondo px-4 py-2.5 text-peligro">
          {errores.general}
        </p>
      )}

      <section className="space-y-4 rounded-3xl border border-borde bg-superficie p-5">
        <h2 className="text-lg font-semibold">¿De qué culto?</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {iglesias.length === 1 ? (
            <div className="text-sm font-semibold">
              Iglesia
              <p className="mt-1.5 py-3 text-base font-normal">{iglesias[0].nombre}</p>
            </div>
          ) : (
            <Campo etiqueta="Iglesia" error={errores.iglesia}>
              <select
                value={iglesia}
                onChange={(e) => setIglesia(e.target.value)}
                aria-invalid={errores.iglesia ? true : undefined}
                className={claseCampo}
              >
                <option value="">Elige la iglesia</option>
                {iglesias.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.nombre}
                  </option>
                ))}
              </select>
            </Campo>
          )}
          <Campo etiqueta="Fecha" error={errores.fecha}>
            <input
              type="date"
              value={fecha}
              max={hoy}
              onChange={(e) => setFecha(e.target.value)}
              aria-invalid={errores.fecha ? true : undefined}
              className={claseCampo}
            />
          </Campo>
          <Campo etiqueta="Culto" ayuda="Opcional: déjalo vacío si fue por fecha.">
            <select
              value={culto}
              onChange={(e) => setCulto(e.target.value as Culto | '')}
              className={claseCampo}
            >
              <option value="">Sin culto específico</option>
              {CULTOS.map((c) => (
                <option key={c.clave} value={c.clave}>
                  {c.nombre}
                </option>
              ))}
            </select>
          </Campo>
        </div>
      </section>

      <section className="space-y-4 rounded-3xl border border-borde bg-superficie p-5">
        <div>
          <h2 className="text-lg font-semibold">Lo recaudado</h2>
          <p className="text-sm text-texto-suave">
            Escribe solo los tipos que hubo. No se registra quién dio, solo la cantidad.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {TIPOS.map((t) => (
            <Campo key={t.clave} etiqueta={t.nombre} error={errores[t.clave]}>
              <span className="relative block">
                <span
                  aria-hidden="true"
                  className="pointer-events-none absolute top-1/2 left-3.5 mt-[3px] -translate-y-1/2 text-texto-suave"
                >
                  $
                </span>
                <input
                  type="text"
                  inputMode="decimal"
                  autoComplete="off"
                  value={montos[t.clave]}
                  onChange={(e) => setMontos((m) => ({ ...m, [t.clave]: e.target.value }))}
                  aria-invalid={errores[t.clave] ? true : undefined}
                  className={claseCampo + ' pl-8 tabular-nums'}
                />
              </span>
            </Campo>
          ))}
        </div>
        {montos.otras.trim() !== '' && (
          <Campo etiqueta="¿De qué fueron las otras donaciones?" error={errores.descripcion}>
            <input
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              autoComplete="off"
              aria-invalid={errores.descripcion ? true : undefined}
              className={claseCampo}
            />
          </Campo>
        )}
      </section>

      <div className="sticky bottom-0 -mx-4 border-t border-borde bg-fondo/85 px-4 py-3 backdrop-blur-md md:static md:mx-0 md:border-0 md:bg-transparent md:p-0 md:backdrop-blur-none">
        <div className="flex items-center gap-3">
          <p className="min-w-0 flex-1" aria-live="polite">
            <span className="block text-sm text-texto-suave">Total</span>
            <span className="font-titulo text-2xl font-bold tabular-nums">
              {formatearMonto(total)}
            </span>
          </p>
          <button type="submit" disabled={guardando} className={claseBotonPrincipal}>
            {guardando ? 'Guardando…' : 'Registrar'}
          </button>
          <button
            type="button"
            onClick={() => navegar('/ingresos')}
            className={claseBotonSecundario}
          >
            Cancelar
          </button>
        </div>
      </div>
    </form>
  )
}

export default function FormularioIngresos() {
  const { estado, reintentar } = useCarga(
    listarIglesiasParaIngresos,
    'preparar el formulario',
    'iglesias',
  )

  return (
    <section>
      <Volver a="/ingresos">Ingresos</Volver>
      {estado.tipo === 'cargando' && (
        <div className="mt-3">
          <Cargando />
        </div>
      )}
      {estado.tipo === 'error' && (
        <div className="mt-3">
          {estado.sinAcceso ? (
            <SinAcceso />
          ) : (
            <ErrorConReintento mensaje={estado.mensaje} reintentar={reintentar} />
          )}
        </div>
      )}
      {estado.tipo === 'listo' && estado.datos.length === 0 && (
        <p className="mt-3 rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
          No tienes iglesias a tu cargo para registrar ingresos.
        </p>
      )}
      {estado.tipo === 'listo' && estado.datos.length > 0 && <Editor iglesias={estado.datos} />}
    </section>
  )
}
