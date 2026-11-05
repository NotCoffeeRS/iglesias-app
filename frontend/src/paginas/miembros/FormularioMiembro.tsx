import { useState, type FormEvent, type ReactNode } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  actualizarMiembro,
  crearMiembro,
  ESTADOS,
  ESTADOS_CIVILES,
  listarIglesiasParaMiembros,
  obtenerMiembro,
  type EstadoCivil,
  type EstadoMiembro,
  type IglesiaOpcion,
  type Miembro,
  type MiembroEntrada,
} from '../../api/miembros'
import { Cargando, ErrorConReintento, Volver } from './comunes'
import {
  claseBotonPrincipal,
  claseBotonSecundario,
  claseCampo,
  hoyEnMerida,
  mensajeDeError,
  useCarga,
} from './utilidades'

interface Formulario {
  nombre: string
  telefono: string
  correo: string
  fecha_nacimiento: string
  direccion: string
  estado_civil: EstadoCivil | ''
  fecha_bautizo: string
  fecha_ingreso: string
  iglesia_id: string
  estado: EstadoMiembro | ''
}

type Campo = keyof Formulario
type Errores = Partial<Record<Campo, string>>

function desdeMiembro(m: Miembro | undefined, iglesias: IglesiaOpcion[]): Formulario {
  return {
    nombre: m?.nombre ?? '',
    telefono: m?.telefono ?? '',
    correo: m?.correo ?? '',
    fecha_nacimiento: m?.fecha_nacimiento ?? '',
    direccion: m?.direccion ?? '',
    estado_civil: m?.estado_civil ?? '',
    fecha_bautizo: m?.fecha_bautizo ?? '',
    fecha_ingreso: m?.fecha_ingreso ?? '',
    // Con una sola iglesia en su alcance, se elige sola.
    iglesia_id: m ? String(m.iglesia_id) : iglesias.length === 1 ? String(iglesias[0].id) : '',
    estado: m?.estado ?? '',
  }
}

const vacioANulo = (texto: string) => (texto.trim() === '' ? null : texto.trim())

function aEntrada(f: Formulario): MiembroEntrada {
  return {
    nombre: f.nombre.trim(),
    telefono: vacioANulo(f.telefono),
    correo: vacioANulo(f.correo),
    fecha_nacimiento: vacioANulo(f.fecha_nacimiento),
    direccion: vacioANulo(f.direccion),
    estado_civil: f.estado_civil || null,
    fecha_bautizo: vacioANulo(f.fecha_bautizo),
    fecha_ingreso: vacioANulo(f.fecha_ingreso),
    iglesia_id: Number(f.iglesia_id),
    estado: f.estado as EstadoMiembro,
  }
}

function validar(f: Formulario): Errores {
  const e: Errores = {}
  const hoy = hoyEnMerida()
  if (!f.nombre.trim()) e.nombre = 'Escribe el nombre completo.'
  if (f.correo.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.correo.trim()))
    e.correo = 'Revisa el correo; debe verse como nombre@ejemplo.com.'
  for (const campo of ['fecha_nacimiento', 'fecha_bautizo', 'fecha_ingreso'] as const) {
    if (f[campo] && f[campo] > hoy) e[campo] = 'No puede ser una fecha futura.'
  }
  if (
    !e.fecha_bautizo &&
    f.fecha_bautizo &&
    f.fecha_nacimiento &&
    f.fecha_bautizo < f.fecha_nacimiento
  )
    e.fecha_bautizo = 'Debe ser después del nacimiento.'
  if (!f.iglesia_id) e.iglesia_id = 'Elige la iglesia.'
  if (!f.estado) e.estado = 'Elige el estado.'
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

function Editor({ miembro, iglesias }: { miembro?: Miembro; iglesias: IglesiaOpcion[] }) {
  const navegar = useNavigate()
  const [f, setF] = useState<Formulario>(() => desdeMiembro(miembro, iglesias))
  const [errores, setErrores] = useState<Errores>({})
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)
  const hoy = hoyEnMerida()

  const cambiar = (campo: Campo, valor: string) => setF((actual) => ({ ...actual, [campo]: valor }))
  const props = (campo: Campo) => ({
    value: f[campo],
    onChange: (e: { target: { value: string } }) => cambiar(campo, e.target.value),
    'aria-invalid': errores[campo] ? true : undefined,
    className: claseCampo,
  })

  async function guardar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const encontrados = validar(f)
    setErrores(encontrados)
    setErrorGeneral(null)
    if (Object.keys(encontrados).length > 0) {
      setErrorGeneral('Revisa los campos marcados.')
      return
    }
    setGuardando(true)
    try {
      if (miembro) await actualizarMiembro(miembro.id, aEntrada(f))
      else await crearMiembro(aEntrada(f))
      navegar('/miembros', {
        replace: true,
        state: { aviso: miembro ? 'Cambios guardados.' : 'Miembro registrado.' },
      })
    } catch (e) {
      setErrorGeneral(
        mensajeDeError(e, miembro ? 'editar este miembro' : 'registrar miembros en esta iglesia'),
      )
      setGuardando(false)
    }
  }

  return (
    <form onSubmit={guardar} noValidate className="mt-3 space-y-5">
      <h1 className="text-3xl font-bold">{miembro ? miembro.nombre : 'Registrar miembro'}</h1>

      {errorGeneral && (
        <p role="alert" className="rounded-xl bg-peligro-fondo px-4 py-2.5 text-peligro">
          {errorGeneral}
        </p>
      )}

      <section className="space-y-4 rounded-3xl border border-borde bg-superficie p-5">
        <h2 className="text-lg font-semibold">Datos personales</h2>
        <Etiqueta texto="Nombre completo" error={errores.nombre}>
          <input autoComplete="off" {...props('nombre')} />
        </Etiqueta>
        <div className="grid gap-4 sm:grid-cols-2">
          <Etiqueta texto="Teléfono" ayuda="Opcional.">
            <input type="tel" autoComplete="off" {...props('telefono')} />
          </Etiqueta>
          <Etiqueta texto="Correo" error={errores.correo} ayuda="Opcional.">
            <input type="email" inputMode="email" autoComplete="off" {...props('correo')} />
          </Etiqueta>
          <Etiqueta texto="Fecha de nacimiento" error={errores.fecha_nacimiento} ayuda="Opcional.">
            <input type="date" max={hoy} {...props('fecha_nacimiento')} />
          </Etiqueta>
          <Etiqueta texto="Estado civil" ayuda="Opcional.">
            <select {...props('estado_civil')}>
              <option value="">Sin indicar</option>
              {ESTADOS_CIVILES.map((e) => (
                <option key={e.clave} value={e.clave}>
                  {e.nombre}
                </option>
              ))}
            </select>
          </Etiqueta>
        </div>
        <Etiqueta texto="Dirección" ayuda="Opcional.">
          <input autoComplete="off" {...props('direccion')} />
        </Etiqueta>
      </section>

      <section className="space-y-4 rounded-3xl border border-borde bg-superficie p-5">
        <h2 className="text-lg font-semibold">En la iglesia</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {iglesias.length === 1 ? (
            <div className="text-sm font-semibold">
              Iglesia
              <p className="mt-1.5 py-3 text-base font-normal">{iglesias[0].nombre}</p>
            </div>
          ) : (
            <Etiqueta texto="Iglesia" error={errores.iglesia_id}>
              <select {...props('iglesia_id')}>
                <option value="">Elige una iglesia</option>
                {iglesias.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.nombre}
                  </option>
                ))}
              </select>
            </Etiqueta>
          )}
          <Etiqueta texto="Estado" error={errores.estado}>
            <select {...props('estado')}>
              <option value="">Elige un estado</option>
              {ESTADOS.map((e) => (
                <option key={e.clave} value={e.clave}>
                  {e.nombre}
                </option>
              ))}
            </select>
          </Etiqueta>
          <Etiqueta
            texto="Forma parte desde"
            error={errores.fecha_ingreso}
            ayuda="Fecha en que se integró a la congregación. Opcional."
          >
            <input type="date" max={hoy} {...props('fecha_ingreso')} />
          </Etiqueta>
          <Etiqueta texto="Fecha de bautizo" error={errores.fecha_bautizo} ayuda="Opcional.">
            <input type="date" max={hoy} {...props('fecha_bautizo')} />
          </Etiqueta>
        </div>
        <p className="text-sm text-texto-suave">La célula se asigna desde Grupos.</p>
      </section>

      <div className="sticky bottom-0 -mx-4 flex gap-3 border-t border-borde bg-fondo/85 px-4 py-3 backdrop-blur-md md:static md:mx-0 md:border-0 md:bg-transparent md:p-0 md:backdrop-blur-none">
        <button
          type="submit"
          disabled={guardando}
          className={claseBotonPrincipal + ' flex-1 md:flex-none'}
        >
          {guardando ? 'Guardando…' : miembro ? 'Guardar cambios' : 'Registrar miembro'}
        </button>
        <button type="button" onClick={() => navegar('/miembros')} className={claseBotonSecundario}>
          Cancelar
        </button>
      </div>
    </form>
  )
}

export default function FormularioMiembro() {
  const { id } = useParams()
  const { estado, reintentar } = useCarga(
    () =>
      Promise.all([
        id ? obtenerMiembro(Number(id)) : Promise.resolve(undefined),
        listarIglesiasParaMiembros(),
      ]),
    id ? 'cargar este miembro' : 'preparar el registro',
    id,
  )

  // Si la dirección cambió de un miembro a otro, los datos que quedan son los del anterior:
  // se ignoran hasta que llegue el que corresponde, para no abrir el formulario con datos ajenos.
  const vigente =
    estado.tipo === 'listo' && (id ? estado.datos[0]?.id === Number(id) : !estado.datos[0])

  return (
    <section>
      <Volver a="/miembros">Miembros</Volver>
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
        <Editor key={id ?? 'nuevo'} miembro={estado.datos[0]} iglesias={estado.datos[1]} />
      )}
    </section>
  )
}
