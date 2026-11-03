import { useState, type FormEvent, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  CATEGORIAS,
  listarIglesiasParaGastos,
  registrarGasto,
  type Categoria,
  type IglesiaOpcion,
} from '../../api/gastos'
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

type Campos = 'iglesia' | 'fecha' | 'categoria' | 'monto' | 'general'
type Errores = Partial<Record<Campos, string>>

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
  const [categoria, setCategoria] = useState<Categoria | ''>('')
  const [monto, setMonto] = useState('')
  const [nota, setNota] = useState('')
  const [errores, setErrores] = useState<Errores>({})
  const [guardando, setGuardando] = useState(false)

  const centavos = leerMonto(monto)

  function validar(): Errores {
    const e: Errores = {}
    if (!iglesia) e.iglesia = 'Elige la iglesia.'
    if (!fecha) e.fecha = 'Indica la fecha.'
    else if (fecha > hoy) e.fecha = 'No puede ser una fecha futura.'
    if (!categoria) e.categoria = 'Elige la categoría.'
    if (!monto.trim()) e.monto = 'Escribe el monto.'
    else if (centavos === null) e.monto = 'Escribe un monto válido, como 1500 o 1500.50.'
    else if (centavos <= 0) e.monto = 'El monto debe ser mayor a 0.'
    return e
  }

  async function guardar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const encontrados = validar()
    setErrores(encontrados)
    if (Object.keys(encontrados).length > 0) return

    setGuardando(true)
    try {
      await registrarGasto({
        iglesia_id: Number(iglesia),
        fecha,
        categoria: categoria as Categoria,
        monto: aTextoMonto(centavos as number),
        nota: nota.trim() || null,
      })
      navegar('/gastos', {
        replace: true,
        state: { aviso: `Gasto registrado: ${formatearMonto(centavos as number)}.` },
      })
    } catch (e) {
      setErrores({ general: mensajeDeError(e, 'registrar gastos en esta iglesia') })
      setGuardando(false)
    }
  }

  return (
    <form onSubmit={guardar} noValidate className="mt-3 space-y-5">
      <h1 className="text-3xl font-bold">Registrar gasto</h1>

      {errores.general && (
        <p role="alert" className="rounded-xl bg-peligro-fondo px-4 py-2.5 text-peligro">
          {errores.general}
        </p>
      )}

      <section className="space-y-4 rounded-3xl border border-borde bg-superficie p-5">
        <h2 className="text-lg font-semibold">¿En qué se gastó?</h2>
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
          <Campo etiqueta="Categoría" error={errores.categoria}>
            <select
              value={categoria}
              onChange={(e) => setCategoria(e.target.value as Categoria | '')}
              aria-invalid={errores.categoria ? true : undefined}
              className={claseCampo}
            >
              <option value="">Elige la categoría</option>
              {CATEGORIAS.map((c) => (
                <option key={c.clave} value={c.clave}>
                  {c.nombre}
                </option>
              ))}
            </select>
          </Campo>
          <Campo etiqueta="Monto" error={errores.monto}>
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
                value={monto}
                onChange={(e) => setMonto(e.target.value)}
                aria-invalid={errores.monto ? true : undefined}
                className={claseCampo + ' pl-8 tabular-nums'}
              />
            </span>
          </Campo>
        </div>
        <Campo etiqueta="Nota" ayuda="Opcional. Por ejemplo: recibo de luz de octubre.">
          <textarea
            value={nota}
            onChange={(e) => setNota(e.target.value)}
            rows={3}
            className={claseCampo}
          />
        </Campo>
      </section>

      <div className="sticky bottom-0 -mx-4 border-t border-borde bg-fondo/85 px-4 py-3 backdrop-blur-md md:static md:mx-0 md:border-0 md:bg-transparent md:p-0 md:backdrop-blur-none">
        <div className="flex items-center gap-3">
          <p className="min-w-0 flex-1" aria-live="polite">
            <span className="block text-sm text-texto-suave">Monto</span>
            <span className="font-titulo text-2xl font-bold tabular-nums">
              {formatearMonto(centavos ?? 0)}
            </span>
          </p>
          <button type="submit" disabled={guardando} className={claseBotonPrincipal}>
            {guardando ? 'Guardando…' : 'Registrar'}
          </button>
          <button type="button" onClick={() => navegar('/gastos')} className={claseBotonSecundario}>
            Cancelar
          </button>
        </div>
      </div>
    </form>
  )
}

export default function FormularioGasto() {
  const { estado, reintentar } = useCarga(
    listarIglesiasParaGastos,
    'preparar el formulario',
    'iglesias',
  )

  return (
    <section>
      <Volver a="/gastos">Gastos</Volver>
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
          No tienes iglesias a tu cargo para registrar gastos.
        </p>
      )}
      {estado.tipo === 'listo' && estado.datos.length > 0 && <Editor iglesias={estado.datos} />}
    </section>
  )
}
