import { useState, type FormEvent, type ReactNode } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  actualizarGrupo,
  crearGrupo,
  listarCandidatos,
  listarIglesiasParaGrupos,
  obtenerGrupo,
  TIPOS_GRUPO,
  type Grupo,
  type GrupoEntrada,
  type Opcion,
  type TipoGrupo,
} from '../../api/grupos'
import { Cargando, ErrorConReintento, Volver } from './comunes'
import {
  claseBotonPrincipal,
  claseBotonSecundario,
  claseCampo,
  mensajeDeError,
  useCarga,
} from './utilidades'

interface Formulario {
  nombre: string
  tipo: TipoGrupo | ''
  iglesia_id: string
  lider_id: string
  asistente_id: string
}

type Errores = Partial<Record<keyof Formulario, string>>

function validar(f: Formulario): Errores {
  const e: Errores = {}
  if (!f.tipo) e.tipo = 'Elige el tipo de grupo.'
  if (!f.nombre.trim()) e.nombre = 'Escribe el nombre del grupo.'
  if (!f.iglesia_id) e.iglesia_id = 'Elige la iglesia.'
  if (!f.lider_id) e.lider_id = 'Elige quién lo dirige.'
  if (f.asistente_id && f.asistente_id === f.lider_id)
    e.asistente_id = 'El asistente debe ser otra persona.'
  return e
}

function Etiqueta({
  texto,
  error,
  ayuda,
  children,
}: {
  texto: string
  error?: string
  ayuda?: string
  children: ReactNode
}) {
  return (
    <label className="block text-sm font-semibold text-texto">
      {texto}
      {children}
      {error ? (
        <span className="mt-1 block font-normal text-peligro">{error}</span>
      ) : (
        ayuda && <span className="mt-1 block font-normal text-texto-suave">{ayuda}</span>
      )}
    </label>
  )
}

/** Selectores de líder y asistente con los miembros de la iglesia elegida. */
function Personas({
  iglesiaId,
  f,
  errores,
  cambiar,
}: {
  iglesiaId: string
  f: Formulario
  errores: Errores
  cambiar: (campo: keyof Formulario, valor: string) => void
}) {
  const { estado, reintentar } = useCarga(
    () => listarCandidatos(Number(iglesiaId)),
    'cargar los miembros de esta iglesia',
    iglesiaId,
  )

  if (estado.tipo === 'cargando')
    return <p className="text-sm text-texto-suave">Cargando miembros de la iglesia…</p>
  if (estado.tipo === 'error')
    return (
      <p role="alert" className="text-sm text-peligro">
        {estado.mensaje}{' '}
        <button type="button" onClick={reintentar} className="font-semibold underline">
          Reintentar
        </button>
      </p>
    )
  if (estado.datos.length === 0)
    return (
      <p className="text-sm text-texto-suave">
        Esta iglesia no tiene miembros registrados. Regístralos primero en Miembros.
      </p>
    )

  const personas = [...estado.datos].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'))
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Etiqueta texto="Líder" error={errores.lider_id}>
        <select
          value={f.lider_id}
          onChange={(e) => cambiar('lider_id', e.target.value)}
          aria-invalid={errores.lider_id ? true : undefined}
          className={claseCampo}
        >
          <option value="">Elige al líder</option>
          {personas.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nombre}
            </option>
          ))}
        </select>
      </Etiqueta>
      <Etiqueta texto="Asistente o segundo" error={errores.asistente_id} ayuda="Opcional.">
        <select
          value={f.asistente_id}
          onChange={(e) => cambiar('asistente_id', e.target.value)}
          aria-invalid={errores.asistente_id ? true : undefined}
          className={claseCampo}
        >
          <option value="">Sin asistente</option>
          {personas.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nombre}
            </option>
          ))}
        </select>
      </Etiqueta>
    </div>
  )
}

function Editor({ grupo, iglesias }: { grupo?: Grupo; iglesias: Opcion[] }) {
  const navegar = useNavigate()
  const [f, setF] = useState<Formulario>({
    nombre: grupo?.nombre ?? '',
    tipo: grupo?.tipo ?? '',
    iglesia_id: grupo
      ? String(grupo.iglesia_id)
      : iglesias.length === 1
        ? String(iglesias[0].id)
        : '',
    lider_id: grupo ? String(grupo.lider_id) : '',
    asistente_id: grupo?.asistente_id ? String(grupo.asistente_id) : '',
  })
  const [errores, setErrores] = useState<Errores>({})
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)

  function cambiar(campo: keyof Formulario, valor: string) {
    setF((actual) =>
      campo === 'iglesia_id'
        ? // Al cambiar de iglesia, el líder y el asistente anteriores ya no aplican.
          { ...actual, iglesia_id: valor, lider_id: '', asistente_id: '' }
        : { ...actual, [campo]: valor },
    )
  }

  async function guardar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const encontrados = validar(f)
    setErrores(encontrados)
    setErrorGeneral(null)
    if (Object.keys(encontrados).length > 0) {
      setErrorGeneral('Revisa los campos marcados.')
      return
    }
    const datos: GrupoEntrada = {
      nombre: f.nombre.trim(),
      tipo: f.tipo as TipoGrupo,
      iglesia_id: Number(f.iglesia_id),
      lider_id: Number(f.lider_id),
      asistente_id: f.asistente_id ? Number(f.asistente_id) : null,
    }
    setGuardando(true)
    try {
      if (grupo) await actualizarGrupo(grupo.id, datos)
      else await crearGrupo(datos)
      navegar('/grupos', {
        replace: true,
        state: { aviso: grupo ? 'Cambios guardados.' : 'Grupo creado.' },
      })
    } catch (e) {
      setErrorGeneral(
        mensajeDeError(e, grupo ? 'editar este grupo' : 'crear grupos en esta iglesia'),
      )
      setGuardando(false)
    }
  }

  const ejemplo = TIPOS_GRUPO.find((t) => t.clave === f.tipo)?.ejemplo

  return (
    <form onSubmit={guardar} noValidate className="mt-3 space-y-5">
      <h1 className="text-3xl font-bold">{grupo ? grupo.nombre : 'Crear grupo'}</h1>

      {errorGeneral && (
        <p role="alert" className="rounded-xl bg-peligro-fondo px-4 py-2.5 text-peligro">
          {errorGeneral}
        </p>
      )}

      <section className="space-y-4 rounded-3xl border border-borde bg-superficie p-5">
        <h2 className="text-lg font-semibold">Grupo</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Etiqueta texto="Tipo" error={errores.tipo}>
            <select
              value={f.tipo}
              onChange={(e) => cambiar('tipo', e.target.value)}
              aria-invalid={errores.tipo ? true : undefined}
              className={claseCampo}
            >
              <option value="">Elige el tipo</option>
              {TIPOS_GRUPO.map((t) => (
                <option key={t.clave} value={t.clave}>
                  {t.nombre}
                </option>
              ))}
            </select>
          </Etiqueta>
          <Etiqueta
            texto="Nombre"
            error={errores.nombre}
            ayuda={ejemplo ? `Por ejemplo: ${ejemplo}.` : undefined}
          >
            <input
              value={f.nombre}
              onChange={(e) => cambiar('nombre', e.target.value)}
              aria-invalid={errores.nombre ? true : undefined}
              className={claseCampo}
            />
          </Etiqueta>
        </div>
        {iglesias.length === 1 ? (
          <p className="text-sm">
            <span className="font-semibold">Iglesia: </span>
            {iglesias[0].nombre}
          </p>
        ) : (
          <Etiqueta texto="Iglesia" error={errores.iglesia_id}>
            <select
              value={f.iglesia_id}
              onChange={(e) => cambiar('iglesia_id', e.target.value)}
              aria-invalid={errores.iglesia_id ? true : undefined}
              className={claseCampo + ' sm:max-w-md'}
            >
              <option value="">Elige la iglesia</option>
              {iglesias.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.nombre}
                </option>
              ))}
            </select>
          </Etiqueta>
        )}
      </section>

      <section className="space-y-4 rounded-3xl border border-borde bg-superficie p-5">
        <h2 className="text-lg font-semibold">Quién lo dirige</h2>
        {f.iglesia_id ? (
          <Personas iglesiaId={f.iglesia_id} f={f} errores={errores} cambiar={cambiar} />
        ) : (
          <p className={errores.lider_id ? 'text-sm text-peligro' : 'text-sm text-texto-suave'}>
            {errores.lider_id ?? 'Elige primero la iglesia para ver a sus miembros.'}
          </p>
        )}
        <p className="text-sm text-texto-suave">
          Los integrantes se asignan aparte (asignaciones).
        </p>
      </section>

      <div className="sticky bottom-0 -mx-4 flex gap-3 border-t border-borde bg-fondo/85 px-4 py-3 backdrop-blur-md md:static md:mx-0 md:border-0 md:bg-transparent md:p-0 md:backdrop-blur-none">
        <button
          type="submit"
          disabled={guardando}
          className={claseBotonPrincipal + ' flex-1 md:flex-none'}
        >
          {guardando ? 'Guardando…' : grupo ? 'Guardar cambios' : 'Crear grupo'}
        </button>
        <button type="button" onClick={() => navegar('/grupos')} className={claseBotonSecundario}>
          Cancelar
        </button>
      </div>
    </form>
  )
}

export default function FormularioGrupo() {
  const { id } = useParams()
  const { estado, reintentar } = useCarga(
    () =>
      Promise.all([
        id ? obtenerGrupo(Number(id)) : Promise.resolve(undefined),
        listarIglesiasParaGrupos(),
      ]),
    id ? 'cargar este grupo' : 'preparar el formulario',
    id,
  )

  // Si la dirección cambió de un grupo a otro, los datos que quedan son los del anterior:
  // se ignoran hasta que llegue el que corresponde, para no abrir el formulario con datos ajenos.
  const vigente =
    estado.tipo === 'listo' && (id ? estado.datos[0]?.id === Number(id) : !estado.datos[0])

  return (
    <section>
      <Volver a="/grupos">Grupos</Volver>
      {(estado.tipo === 'cargando' || (estado.tipo === 'listo' && !vigente)) && (
        <div className="mt-3">
          <Cargando />
        </div>
      )}
      {estado.tipo === 'error' && (
        <div className="mt-3">
          <ErrorConReintento mensaje={estado.mensaje} reintentar={reintentar} />
        </div>
      )}
      {estado.tipo === 'listo' && vigente && (
        <Editor key={id ?? 'nuevo'} grupo={estado.datos[0]} iglesias={estado.datos[1]} />
      )}
    </section>
  )
}
