import { useState, type FormEvent, type ReactNode } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  editarComunicado,
  listarIglesiasParaComunicados,
  obtenerComunicado,
  publicarComunicado,
  type Comunicado,
  type IglesiaOpcion,
} from '../../api/comunicados'
import { Cargando, ErrorConReintento, Volver } from './comunes'
import {
  claseBotonPrincipal,
  claseBotonSecundario,
  claseCampo,
  hoyEnMerida,
  mensajeDeError,
  useCarga,
} from './utilidades'

const TODO_EL_PRESBITERIO = 'todo'

type Errores = Partial<Record<'titulo' | 'contenido' | 'vigencia' | 'iglesia' | 'general', string>>

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

function Editor({ iglesias, comunicado }: { iglesias: IglesiaOpcion[]; comunicado?: Comunicado }) {
  const navegar = useNavigate()
  const hoy = hoyEnMerida()
  const [titulo, setTitulo] = useState(comunicado?.titulo ?? '')
  const [contenido, setContenido] = useState(comunicado?.contenido ?? '')
  const [vigencia, setVigencia] = useState(comunicado?.vigente_hasta ?? '')
  const [iglesia, setIglesia] = useState(
    comunicado
      ? comunicado.iglesia_id === null
        ? TODO_EL_PRESBITERIO
        : String(comunicado.iglesia_id)
      : iglesias.length === 1
        ? String(iglesias[0].id)
        : '',
  )
  const [errores, setErrores] = useState<Errores>({})
  const [guardando, setGuardando] = useState(false)

  function validar(): Errores {
    const e: Errores = {}
    if (!titulo.trim()) e.titulo = 'Escribe el título del comunicado.'
    else if (titulo.trim().length > 150) e.titulo = 'Usa 150 letras como máximo.'
    if (!contenido.trim()) e.contenido = 'Escribe el contenido del comunicado.'
    else if (contenido.trim().length > 5000) e.contenido = 'Usa 5000 letras como máximo.'
    if (!vigencia) e.vigencia = 'Indica hasta cuándo estará vigente.'
    else if (vigencia < hoy) e.vigencia = 'La vigencia no puede terminar antes de hoy.'
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
      contenido: contenido.trim(),
      iglesia_id: iglesia === TODO_EL_PRESBITERIO ? null : Number(iglesia),
      vigente_hasta: vigencia,
    }
    setGuardando(true)
    try {
      if (comunicado) await editarComunicado(comunicado.id, datos)
      else await publicarComunicado(datos)
      navegar('/comunicados', {
        replace: true,
        state: { aviso: comunicado ? 'Comunicado actualizado.' : 'Comunicado publicado.' },
      })
    } catch (e) {
      setErrores({ general: mensajeDeError(e, 'guardar el comunicado') })
      setGuardando(false)
    }
  }

  return (
    <form onSubmit={guardar} noValidate className="mt-3 space-y-5">
      <h1 className="text-3xl font-bold">
        {comunicado ? 'Editar comunicado' : 'Nuevo comunicado'}
      </h1>

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
        <Campo etiqueta="Contenido" error={errores.contenido}>
          <textarea
            value={contenido}
            onChange={(e) => setContenido(e.target.value)}
            rows={6}
            maxLength={5000}
            aria-invalid={errores.contenido ? true : undefined}
            className={claseCampo}
          />
        </Campo>
        <div className="grid gap-4 sm:grid-cols-2">
          <Campo
            etiqueta="Vigente hasta"
            error={errores.vigencia}
            ayuda="Último día en que se muestra."
          >
            <input
              type="date"
              value={vigencia}
              min={hoy}
              onChange={(e) => setVigencia(e.target.value)}
              aria-invalid={errores.vigencia ? true : undefined}
              className={claseCampo}
            />
          </Campo>
          <Campo
            etiqueta="Para"
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
        </div>
      </section>

      <div className="flex items-center gap-3">
        <button type="submit" disabled={guardando} className={claseBotonPrincipal}>
          {guardando ? 'Guardando…' : comunicado ? 'Guardar cambios' : 'Publicar'}
        </button>
        <button
          type="button"
          onClick={() => navegar('/comunicados')}
          className={claseBotonSecundario}
        >
          Cancelar
        </button>
      </div>
    </form>
  )
}

export default function FormularioComunicado() {
  const { id } = useParams()
  const numero = id ? Number(id) : null
  const { estado, reintentar } = useCarga(
    async () => ({
      iglesias: await listarIglesiasParaComunicados(),
      comunicado: numero ? await obtenerComunicado(numero) : undefined,
    }),
    'preparar el formulario',
    `comunicado-${numero ?? 'nuevo'}`,
  )

  return (
    <section>
      <Volver a="/comunicados">Comunicados</Volver>
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
      {estado.tipo === 'listo' && estado.datos.comunicado && !estado.datos.comunicado.vigente && (
        <p className="mt-3 rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
          Este comunicado ya venció y no se puede editar.
        </p>
      )}
      {estado.tipo === 'listo' &&
        !(estado.datos.comunicado && !estado.datos.comunicado.vigente) && (
          <Editor iglesias={estado.datos.iglesias} comunicado={estado.datos.comunicado} />
        )}
    </section>
  )
}
