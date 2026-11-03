import { useState, type FormEvent, type ReactNode } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  actualizarIglesia,
  obtenerIglesia,
  type Iglesia,
  type IglesiaEntrada,
  type TipoRed,
} from '../../api/iglesias'
import {
  Cargando,
  claseBotonPrincipal,
  claseBotonSecundario,
  claseCampo,
  ErrorConReintento,
  Volver,
} from './comunes'
import { esEnlaceSeguro, mensajeDeError, useCarga } from './utilidades'

// Clave local para que React distinga filas nuevas que aún no tienen id del servidor.
let siguienteClave = 1
const nuevaClave = () => `n${siguienteClave++}`

interface SedeForm {
  clave: string
  id?: number
  nombre: string
  direccion: string
  enlace_maps: string
}

interface RedForm {
  clave: string
  id?: number
  nombre: string
  url: string
  tipo: TipoRed
}

interface Formulario {
  nombre: string
  foto_url: string
  pastor: string
  telefono_pastor: string
  telefono_iglesia: string
  sedes: SedeForm[]
  redes: RedForm[]
}

type Errores = Record<string, string>

function desdeIglesia(i: Iglesia): Formulario {
  return {
    nombre: i.nombre,
    foto_url: i.foto_url ?? '',
    pastor: i.pastor ?? '',
    telefono_pastor: i.telefono_pastor ?? '',
    telefono_iglesia: i.telefono_iglesia ?? '',
    sedes: i.sedes.map((s) => ({
      clave: nuevaClave(),
      id: s.id,
      nombre: s.nombre,
      direccion: s.direccion,
      enlace_maps: s.enlace_maps ?? '',
    })),
    redes: i.redes.map((r) => ({ clave: nuevaClave(), ...r })),
  }
}

const vacioANulo = (texto: string) => (texto.trim() === '' ? null : texto.trim())

function aEntrada(f: Formulario): IglesiaEntrada {
  return {
    nombre: f.nombre.trim(),
    foto_url: vacioANulo(f.foto_url),
    pastor: vacioANulo(f.pastor),
    telefono_pastor: vacioANulo(f.telefono_pastor),
    telefono_iglesia: vacioANulo(f.telefono_iglesia),
    sedes: f.sedes.map(({ id, nombre, direccion, enlace_maps }) => ({
      id,
      nombre: nombre.trim(),
      direccion: direccion.trim(),
      enlace_maps: vacioANulo(enlace_maps),
    })),
    redes: f.redes.map(({ id, nombre, url, tipo }) => ({
      id,
      nombre: nombre.trim(),
      url: url.trim(),
      tipo,
    })),
  }
}

const ENLACE_INVALIDO = 'Debe empezar con https:// (cópialo desde el navegador).'

function validar(f: Formulario): Errores {
  const e: Errores = {}
  if (!f.nombre.trim()) e.nombre = 'Escribe el nombre de la iglesia.'
  if (f.foto_url.trim() && !esEnlaceSeguro(f.foto_url.trim())) e.foto_url = ENLACE_INVALIDO
  if (f.sedes.length === 0) e.sedes = 'La iglesia necesita al menos una sede.'
  f.sedes.forEach((s) => {
    if (!s.nombre.trim()) e[`${s.clave}.nombre`] = 'Escribe el nombre de la sede.'
    if (!s.direccion.trim()) e[`${s.clave}.direccion`] = 'Escribe la dirección.'
    if (s.enlace_maps.trim() && !esEnlaceSeguro(s.enlace_maps.trim()))
      e[`${s.clave}.enlace_maps`] = ENLACE_INVALIDO
  })
  f.redes.forEach((r) => {
    if (!r.nombre.trim()) e[`${r.clave}.nombre`] = 'Escribe el nombre (p. ej. Facebook).'
    if (!esEnlaceSeguro(r.url.trim())) e[`${r.clave}.url`] = ENLACE_INVALIDO
  })
  return e
}

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
    <label className="block text-sm font-semibold text-texto">
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

function Editor({ iglesia }: { iglesia: Iglesia }) {
  const navegar = useNavigate()
  const [f, setF] = useState<Formulario>(() => desdeIglesia(iglesia))
  const [errores, setErrores] = useState<Errores>({})
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)

  const cambiar = <K extends keyof Formulario>(campo: K, valor: Formulario[K]) =>
    setF((actual) => ({ ...actual, [campo]: valor }))

  const cambiarSede = (clave: string, campo: keyof SedeForm, valor: string) =>
    cambiar(
      'sedes',
      f.sedes.map((s) => (s.clave === clave ? { ...s, [campo]: valor } : s)),
    )

  const cambiarRed = (clave: string, campo: keyof RedForm, valor: string) =>
    cambiar(
      'redes',
      f.redes.map((r) => (r.clave === clave ? { ...r, [campo]: valor } : r)),
    )

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
      await actualizarIglesia(iglesia.id, aEntrada(f))
      navegar(`/iglesias/${iglesia.id}`, { replace: true, state: { guardada: true } })
    } catch (e) {
      setErrorGeneral(mensajeDeError(e, 'editar esta iglesia'))
      setGuardando(false)
    }
  }

  const props = (clave: string) => ({
    'aria-invalid': errores[clave] ? true : undefined,
    className: claseCampo,
  })

  return (
    <form onSubmit={guardar} noValidate className="mt-3 space-y-6">
      <h1 className="text-3xl font-bold">Editar {iglesia.nombre}</h1>

      {errorGeneral && (
        <p role="alert" className="rounded-xl bg-peligro-fondo px-4 py-2.5 text-peligro">
          {errorGeneral}
        </p>
      )}

      <section className="space-y-4 rounded-3xl border border-borde bg-superficie p-5">
        <h2 className="text-lg font-semibold">Datos generales</h2>
        <Campo etiqueta="Nombre" error={errores.nombre}>
          <input
            value={f.nombre}
            onChange={(e) => cambiar('nombre', e.target.value)}
            {...props('nombre')}
          />
        </Campo>
        <Campo
          etiqueta="Foto de la fachada (enlace)"
          error={errores.foto_url}
          ayuda="Opcional. Pega el enlace de una foto publicada en internet."
        >
          <input
            type="url"
            inputMode="url"
            value={f.foto_url}
            onChange={(e) => cambiar('foto_url', e.target.value)}
            {...props('foto_url')}
          />
        </Campo>
        <Campo etiqueta="Pastor">
          <input
            value={f.pastor}
            onChange={(e) => cambiar('pastor', e.target.value)}
            {...props('pastor')}
          />
        </Campo>
        <div className="grid gap-4 sm:grid-cols-2">
          <Campo etiqueta="Teléfono de la iglesia" ayuda="Opcional.">
            <input
              type="tel"
              value={f.telefono_iglesia}
              onChange={(e) => cambiar('telefono_iglesia', e.target.value)}
              {...props('telefono_iglesia')}
            />
          </Campo>
          <Campo etiqueta="Teléfono del pastor" ayuda="Opcional. No se publica.">
            <input
              type="tel"
              value={f.telefono_pastor}
              onChange={(e) => cambiar('telefono_pastor', e.target.value)}
              {...props('telefono_pastor')}
            />
          </Campo>
        </div>
      </section>

      <section className="space-y-3 rounded-3xl border border-borde bg-superficie p-5">
        <h2 className="text-lg font-semibold">Sedes</h2>
        {errores.sedes && <p className="text-sm text-peligro">{errores.sedes}</p>}
        {f.sedes.map((s, i) => (
          <div key={s.clave} className="space-y-3 rounded-2xl bg-superficie-2 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="font-semibold">Sede {i + 1}</p>
              <button
                type="button"
                disabled={f.sedes.length === 1}
                onClick={() =>
                  cambiar(
                    'sedes',
                    f.sedes.filter((x) => x.clave !== s.clave),
                  )
                }
                className="rounded-xl px-3 py-1.5 text-sm font-semibold text-peligro hover:bg-peligro-fondo disabled:invisible"
              >
                Quitar sede
              </button>
            </div>
            <Campo etiqueta="Nombre de la sede" error={errores[`${s.clave}.nombre`]}>
              <input
                value={s.nombre}
                onChange={(e) => cambiarSede(s.clave, 'nombre', e.target.value)}
                {...props(`${s.clave}.nombre`)}
              />
            </Campo>
            <Campo etiqueta="Dirección" error={errores[`${s.clave}.direccion`]}>
              <input
                value={s.direccion}
                onChange={(e) => cambiarSede(s.clave, 'direccion', e.target.value)}
                {...props(`${s.clave}.direccion`)}
              />
            </Campo>
            <Campo
              etiqueta="Enlace de Google Maps"
              error={errores[`${s.clave}.enlace_maps`]}
              ayuda="En Google Maps: Compartir → Copiar enlace."
            >
              <input
                type="url"
                inputMode="url"
                value={s.enlace_maps}
                onChange={(e) => cambiarSede(s.clave, 'enlace_maps', e.target.value)}
                {...props(`${s.clave}.enlace_maps`)}
              />
            </Campo>
          </div>
        ))}
        <button
          type="button"
          onClick={() =>
            cambiar('sedes', [
              ...f.sedes,
              { clave: nuevaClave(), nombre: '', direccion: '', enlace_maps: '' },
            ])
          }
          className={claseBotonSecundario}
        >
          Agregar sede
        </button>
      </section>

      <section className="space-y-3 rounded-3xl border border-borde bg-superficie p-5">
        <h2 className="text-lg font-semibold">Redes sociales</h2>
        {f.redes.length === 0 && <p className="text-sm text-texto-suave">Sin redes registradas.</p>}
        {f.redes.map((r) => (
          <div key={r.clave} className="space-y-3 rounded-2xl bg-superficie-2 p-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <Campo etiqueta="Nombre" error={errores[`${r.clave}.nombre`]}>
                <input
                  value={r.nombre}
                  placeholder="Facebook"
                  onChange={(e) => cambiarRed(r.clave, 'nombre', e.target.value)}
                  {...props(`${r.clave}.nombre`)}
                />
              </Campo>
              <Campo etiqueta="Tipo">
                <select
                  value={r.tipo}
                  onChange={(e) => cambiarRed(r.clave, 'tipo', e.target.value)}
                  className={claseCampo}
                >
                  <option value="propia">De la iglesia</option>
                  <option value="relacionada">Relacionada</option>
                </select>
              </Campo>
            </div>
            <Campo etiqueta="Enlace" error={errores[`${r.clave}.url`]}>
              <input
                type="url"
                inputMode="url"
                value={r.url}
                onChange={(e) => cambiarRed(r.clave, 'url', e.target.value)}
                {...props(`${r.clave}.url`)}
              />
            </Campo>
            <button
              type="button"
              onClick={() =>
                cambiar(
                  'redes',
                  f.redes.filter((x) => x.clave !== r.clave),
                )
              }
              className="rounded-xl px-3 py-1.5 text-sm font-semibold text-peligro hover:bg-peligro-fondo"
            >
              Quitar red
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={() =>
            cambiar('redes', [
              ...f.redes,
              { clave: nuevaClave(), nombre: '', url: '', tipo: 'propia' },
            ])
          }
          className={claseBotonSecundario}
        >
          Agregar red
        </button>
      </section>

      <div className="sticky bottom-0 -mx-4 flex gap-3 border-t border-borde bg-fondo/85 px-4 py-3 backdrop-blur-md md:static md:mx-0 md:border-0 md:bg-transparent md:p-0 md:backdrop-blur-none">
        <button
          type="submit"
          disabled={guardando}
          className={claseBotonPrincipal + ' flex-1 md:flex-none'}
        >
          {guardando ? 'Guardando…' : 'Guardar cambios'}
        </button>
        <button
          type="button"
          onClick={() => navegar(`/iglesias/${iglesia.id}`)}
          className={claseBotonSecundario}
        >
          Cancelar
        </button>
      </div>
    </form>
  )
}

export default function FormularioIglesia() {
  const { id } = useParams()
  const { estado, reintentar } = useCarga(() => obtenerIglesia(Number(id)), 'cargar la iglesia', id)

  return (
    <section>
      <Volver a={`/iglesias/${id}`}>Volver a la ficha</Volver>
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
      {estado.tipo === 'listo' && <Editor iglesia={estado.datos} />}
    </section>
  )
}
