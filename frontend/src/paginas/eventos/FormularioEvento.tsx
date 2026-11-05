import { useState, type FormEvent, type ReactNode } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  crearEvento,
  editarEvento,
  listarIglesiasParaEventos,
  obtenerEvento,
  type Evento,
  type IglesiaOpcion,
} from '../../api/eventos'
import { Cargando, ErrorConReintento, Volver } from './comunes'
import {
  claseBotonPrincipal,
  claseBotonSecundario,
  claseCampo,
  hoyEnMerida,
  horaCorta,
  mensajeDeError,
  useCarga,
} from './utilidades'

const TODO_EL_PRESBITERIO = 'todo'

type Campos = 'titulo' | 'fecha' | 'hora' | 'general'
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

function Editor({ iglesias, evento }: { iglesias: IglesiaOpcion[]; evento?: Evento }) {
  const navegar = useNavigate()
  const hoy = hoyEnMerida()
  const [titulo, setTitulo] = useState(evento?.titulo ?? '')
  const [fecha, setFecha] = useState(evento?.fecha ?? hoy)
  const [hora, setHora] = useState(evento ? horaCorta(evento.hora) : '')
  const [iglesia, setIglesia] = useState(
    evento
      ? evento.iglesia_id === null
        ? TODO_EL_PRESBITERIO
        : String(evento.iglesia_id)
      : iglesias.length === 1
        ? String(iglesias[0].id)
        : '',
  )
  const [lugar, setLugar] = useState(evento?.lugar ?? '')
  const [descripcion, setDescripcion] = useState(evento?.descripcion ?? '')
  const [errores, setErrores] = useState<Errores & { iglesia?: string }>({})
  const [guardando, setGuardando] = useState(false)

  function validar() {
    const e: Errores & { iglesia?: string } = {}
    if (!titulo.trim()) e.titulo = 'Escribe el título del evento.'
    else if (titulo.trim().length > 150) e.titulo = 'Usa 150 letras como máximo.'
    if (!fecha) e.fecha = 'Indica la fecha.'
    else if (!evento && fecha < hoy) e.fecha = 'La fecha no puede ser anterior a hoy.'
    if (!hora) e.hora = 'Indica la hora.'
    if (!iglesia) e.iglesia = 'Elige la iglesia o "Todo el Presbiterio".'
    return e
  }

  async function guardar(ev: FormEvent<HTMLFormElement>) {
    ev.preventDefault()
    const encontrados = validar()
    setErrores(encontrados)
    if (Object.keys(encontrados).length > 0) return

    const datos = {
      titulo: titulo.trim(),
      fecha,
      hora,
      iglesia_id: iglesia === TODO_EL_PRESBITERIO ? null : Number(iglesia),
      lugar: lugar.trim() || null,
      descripcion: descripcion.trim() || null,
    }
    setGuardando(true)
    try {
      if (evento) await editarEvento(evento.id, datos)
      else await crearEvento(datos)
      navegar('/eventos', {
        replace: true,
        state: { aviso: evento ? 'Evento actualizado.' : 'Evento creado.' },
      })
    } catch (e) {
      setErrores({ general: mensajeDeError(e, 'guardar el evento') })
      setGuardando(false)
    }
  }

  return (
    <form onSubmit={guardar} noValidate className="mt-3 space-y-5">
      <h1 className="text-3xl font-bold">{evento ? 'Editar evento' : 'Nuevo evento'}</h1>

      {errores.general && (
        <p role="alert" className="rounded-xl bg-peligro-fondo px-4 py-2.5 text-peligro">
          {errores.general}
        </p>
      )}

      <section className="space-y-4 rounded-3xl border border-borde bg-superficie p-5">
        <Campo etiqueta="Título" error={errores.titulo}>
          <input
            type="text"
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            maxLength={150}
            aria-invalid={errores.titulo ? true : undefined}
            className={claseCampo}
          />
        </Campo>
        <div className="grid gap-4 sm:grid-cols-2">
          <Campo etiqueta="Fecha" error={errores.fecha}>
            <input
              type="date"
              value={fecha}
              min={evento ? undefined : hoy}
              onChange={(e) => setFecha(e.target.value)}
              aria-invalid={errores.fecha ? true : undefined}
              className={claseCampo}
            />
          </Campo>
          <Campo etiqueta="Hora" error={errores.hora}>
            <input
              type="time"
              value={hora}
              onChange={(e) => setHora(e.target.value)}
              aria-invalid={errores.hora ? true : undefined}
              className={claseCampo}
            />
          </Campo>
        </div>
        <Campo
          etiqueta="Iglesia"
          error={errores.iglesia}
          ayuda='"Todo el Presbiterio" solo lo puede elegir el presbítero.'
        >
          <select
            value={iglesia}
            onChange={(e) => setIglesia(e.target.value)}
            aria-invalid={errores.iglesia ? true : undefined}
            className={claseCampo}
          >
            <option value="">Elige la iglesia</option>
            <option value={TODO_EL_PRESBITERIO}>Todo el Presbiterio</option>
            {iglesias.map((i) => (
              <option key={i.id} value={i.id}>
                {i.nombre}
              </option>
            ))}
          </select>
        </Campo>
        <Campo etiqueta="Lugar" ayuda="Opcional. Por ejemplo: el templo o un salón.">
          <input
            type="text"
            value={lugar}
            onChange={(e) => setLugar(e.target.value)}
            maxLength={200}
            className={claseCampo}
          />
        </Campo>
        <Campo etiqueta="Descripción" ayuda="Opcional.">
          <textarea
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            rows={4}
            className={claseCampo}
          />
        </Campo>
      </section>

      <div className="flex items-center gap-3">
        <button type="submit" disabled={guardando} className={claseBotonPrincipal}>
          {guardando ? 'Guardando…' : evento ? 'Guardar cambios' : 'Crear evento'}
        </button>
        <button type="button" onClick={() => navegar('/eventos')} className={claseBotonSecundario}>
          Cancelar
        </button>
      </div>
    </form>
  )
}

export default function FormularioEvento() {
  const { id } = useParams()
  const numero = id ? Number(id) : null
  const { estado, reintentar } = useCarga(
    async () => ({
      iglesias: await listarIglesiasParaEventos(),
      evento: numero ? await obtenerEvento(numero) : undefined,
    }),
    'preparar el formulario',
    `evento-${numero ?? 'nuevo'}`,
  )

  return (
    <section>
      <Volver a="/eventos">Eventos</Volver>
      {estado.tipo === 'cargando' && (
        <div className="mt-3">
          <Cargando />
        </div>
      )}
      {estado.tipo === 'error' && (
        <div className="mt-3">
          <ErrorConReintento mensaje={estado.mensaje} reintentar={reintentar} />
        </div>
      )}
      {estado.tipo === 'listo' && estado.datos.evento?.cancelado && (
        <p className="mt-3 rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
          Este evento está cancelado y ya no se puede editar.
        </p>
      )}
      {estado.tipo === 'listo' && !estado.datos.evento?.cancelado && (
        <Editor iglesias={estado.datos.iglesias} evento={estado.datos.evento} />
      )}
    </section>
  )
}
