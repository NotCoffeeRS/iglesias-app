import { useState, type FormEvent, type ReactNode } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  actualizarUsuario,
  crearUsuario,
  listarIglesiasParaUsuarios,
  obtenerUsuario,
  obtenerYo,
  type Cargo,
  type IglesiaOpcion,
  type Usuario,
  type Yo,
} from '../../api/usuarios'
import { Cargando, ErrorConReintento, SinPermiso, Volver } from './comunes'
import {
  cargoBloqueado,
  cargosAsignables,
  iglesiasAsignables,
  puedeEditarA,
  puedeGestionar,
} from './reglas'
import {
  claseBotonPrincipal,
  claseBotonSecundario,
  claseCampo,
  mensajeDeError,
  nombreCargo,
  useCarga,
} from './utilidades'

interface Formulario {
  nombre_usuario: string
  nombre_completo: string
  cargo: Cargo | ''
  iglesia_id: string
  contrasena: string
  activo: boolean
}

type Errores = Partial<Record<keyof Formulario, string>>

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

function Editor({
  yo,
  usuario,
  iglesias,
}: {
  yo: Yo
  usuario?: Usuario
  iglesias: IglesiaOpcion[]
}) {
  const navegar = useNavigate()
  const asignables = cargosAsignables(yo)
  const opcionesIglesia = iglesiasAsignables(yo, iglesias)
  const propia = usuario?.id === yo.id
  const cargoFijo = usuario ? cargoBloqueado(yo, usuario) : false
  const esPresbitero = usuario?.cargo === 'presbitero'
  const iglesiaFija = esPresbitero || opcionesIglesia.length === 1

  const [f, setF] = useState<Formulario>({
    nombre_usuario: usuario?.nombre_usuario ?? '',
    nombre_completo: usuario?.nombre_completo ?? '',
    cargo: usuario?.cargo ?? '',
    iglesia_id: usuario
      ? String(usuario.iglesia_id ?? '')
      : opcionesIglesia.length === 1
        ? String(opcionesIglesia[0].id)
        : '',
    contrasena: '',
    activo: usuario?.activo ?? true,
  })
  const [errores, setErrores] = useState<Errores>({})
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)

  const cambiar = <K extends keyof Formulario>(campo: K, valor: Formulario[K]) =>
    setF((actual) => ({ ...actual, [campo]: valor }))

  function validar(): Errores {
    const e: Errores = {}
    if (!usuario && !f.nombre_usuario.trim()) e.nombre_usuario = 'Escribe el nombre de usuario.'
    if (!f.nombre_completo.trim()) e.nombre_completo = 'Escribe el nombre completo.'
    if (!f.cargo) e.cargo = 'Elige el cargo.'
    if (!esPresbitero && !f.iglesia_id) e.iglesia_id = 'Elige la iglesia.'
    if (!usuario && !f.contrasena) e.contrasena = 'Escribe una contraseña para la cuenta.'
    return e
  }

  async function guardar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const encontrados = validar()
    setErrores(encontrados)
    setErrorGeneral(null)
    if (Object.keys(encontrados).length > 0) {
      setErrorGeneral('Revisa los campos marcados.')
      return
    }
    setGuardando(true)
    try {
      if (usuario) {
        await actualizarUsuario(usuario.id, {
          nombre_completo: f.nombre_completo.trim(),
          cargo: f.cargo as Cargo,
          iglesia_id: esPresbitero ? null : Number(f.iglesia_id),
          activo: f.activo,
        })
      } else {
        await crearUsuario({
          nombre_usuario: f.nombre_usuario.trim(),
          nombre_completo: f.nombre_completo.trim(),
          cargo: f.cargo as Cargo,
          iglesia_id: Number(f.iglesia_id),
          contrasena: f.contrasena,
        })
      }
      navegar('/usuarios', {
        replace: true,
        state: { aviso: usuario ? 'Cambios guardados.' : 'Usuario creado.' },
      })
    } catch (e) {
      setErrorGeneral(
        mensajeDeError(e, usuario ? 'editar este usuario' : 'crear usuarios con ese cargo'),
      )
      setGuardando(false)
    }
  }

  const ayudaCargo = !cargoFijo
    ? undefined
    : propia
      ? 'Nadie cambia su propio cargo desde aquí.'
      : 'Tu cargo no puede asignar este cargo.'

  return (
    <form onSubmit={guardar} noValidate className="mt-3 space-y-5">
      <h1 className="text-3xl font-bold">{usuario ? usuario.nombre_completo : 'Crear usuario'}</h1>

      {errorGeneral && (
        <p role="alert" className="rounded-xl bg-peligro-fondo px-4 py-2.5 text-peligro">
          {errorGeneral}
        </p>
      )}

      <section className="space-y-4 rounded-3xl border border-borde bg-superficie p-5">
        <h2 className="text-lg font-semibold">Cuenta</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Etiqueta texto="Nombre completo" error={errores.nombre_completo}>
            <input
              value={f.nombre_completo}
              onChange={(e) => cambiar('nombre_completo', e.target.value)}
              autoComplete="off"
              aria-invalid={errores.nombre_completo ? true : undefined}
              className={claseCampo}
            />
          </Etiqueta>
          <Etiqueta
            texto="Nombre de usuario"
            error={errores.nombre_usuario}
            ayuda={
              usuario ? 'No se puede cambiar.' : 'Con él inicia sesión. No distingue mayúsculas.'
            }
          >
            <input
              value={f.nombre_usuario}
              onChange={(e) => cambiar('nombre_usuario', e.target.value)}
              disabled={!!usuario}
              autoComplete="off"
              autoCapitalize="none"
              autoCorrect="off"
              aria-invalid={errores.nombre_usuario ? true : undefined}
              className={claseCampo}
            />
          </Etiqueta>
        </div>
        {!usuario && (
          <Etiqueta
            texto="Contraseña"
            error={errores.contrasena}
            ayuda="Entrégala a la persona. No se vuelve a mostrar."
          >
            <input
              type="password"
              value={f.contrasena}
              onChange={(e) => cambiar('contrasena', e.target.value)}
              autoComplete="new-password"
              aria-invalid={errores.contrasena ? true : undefined}
              className={claseCampo + ' sm:max-w-sm'}
            />
          </Etiqueta>
        )}
      </section>

      <section className="space-y-4 rounded-3xl border border-borde bg-superficie p-5">
        <h2 className="text-lg font-semibold">Cargo e iglesia</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Etiqueta texto="Cargo" error={errores.cargo} ayuda={ayudaCargo}>
            {cargoFijo && usuario ? (
              <select disabled value={usuario.cargo} className={claseCampo}>
                <option value={usuario.cargo}>{nombreCargo(usuario.cargo)}</option>
              </select>
            ) : (
              <select
                value={f.cargo}
                onChange={(e) => cambiar('cargo', e.target.value as Cargo)}
                aria-invalid={errores.cargo ? true : undefined}
                className={claseCampo}
              >
                <option value="">Elige el cargo</option>
                {asignables.map((c) => (
                  <option key={c} value={c}>
                    {nombreCargo(c)}
                  </option>
                ))}
              </select>
            )}
          </Etiqueta>
          <Etiqueta
            texto="Iglesia"
            error={errores.iglesia_id}
            ayuda={esPresbitero ? 'El presbítero ve todas las iglesias.' : undefined}
          >
            {esPresbitero ? (
              <select disabled className={claseCampo}>
                <option>Todas las iglesias</option>
              </select>
            ) : (
              <select
                value={f.iglesia_id}
                onChange={(e) => cambiar('iglesia_id', e.target.value)}
                disabled={iglesiaFija}
                aria-invalid={errores.iglesia_id ? true : undefined}
                className={claseCampo}
              >
                {!iglesiaFija && <option value="">Elige la iglesia</option>}
                {opcionesIglesia.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.nombre}
                  </option>
                ))}
              </select>
            )}
          </Etiqueta>
        </div>

        {usuario && (
          <label className="flex items-start gap-3 text-sm">
            <input
              type="checkbox"
              checked={f.activo}
              onChange={(e) => cambiar('activo', e.target.checked)}
              disabled={propia}
              className="mt-0.5 h-6 w-6 shrink-0 accent-primario"
            />
            <span>
              <span className="font-semibold">Cuenta activa</span>
              <span className="block text-texto-suave">
                {propia
                  ? 'No puedes desactivar tu propia cuenta.'
                  : 'Si la desactivas, la persona ya no puede entrar. La cuenta no se borra.'}
              </span>
            </span>
          </label>
        )}
        <p className="text-sm text-texto-suave">
          El área se define al asignar a la persona a un grupo (Grupos).
        </p>
      </section>

      <div className="sticky bottom-0 -mx-4 flex gap-3 border-t border-borde bg-fondo/85 px-4 py-3 backdrop-blur-md md:static md:mx-0 md:border-0 md:bg-transparent md:p-0 md:backdrop-blur-none">
        <button
          type="submit"
          disabled={guardando}
          className={claseBotonPrincipal + ' flex-1 md:flex-none'}
        >
          {guardando ? 'Guardando…' : usuario ? 'Guardar cambios' : 'Crear usuario'}
        </button>
        <button type="button" onClick={() => navegar('/usuarios')} className={claseBotonSecundario}>
          Cancelar
        </button>
      </div>
    </form>
  )
}

export default function FormularioUsuario() {
  const { id } = useParams()
  const { estado, reintentar } = useCarga(
    () =>
      Promise.all([
        obtenerYo(),
        id ? obtenerUsuario(Number(id)) : Promise.resolve(undefined),
        listarIglesiasParaUsuarios(),
      ]),
    id ? 'cargar este usuario' : 'preparar el formulario',
    id,
  )

  // Si la dirección cambió de un usuario a otro, los datos que quedan son los del anterior:
  // se ignoran hasta que llegue el que corresponde, para no abrir el formulario con datos ajenos.
  const vigente =
    estado.tipo === 'listo' && (id ? estado.datos[1]?.id === Number(id) : !estado.datos[1])
  const datos = estado.tipo === 'listo' && vigente ? estado.datos : null
  const permitido = datos
    ? datos[1]
      ? puedeEditarA(datos[0], datos[1])
      : puedeGestionar(datos[0])
    : true

  return (
    <section>
      <Volver a="/usuarios">Usuarios</Volver>
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
      {datos && !permitido && (
        <div className="mt-3">
          <SinPermiso />
        </div>
      )}
      {datos && permitido && (
        <Editor key={id ?? 'nuevo'} yo={datos[0]} usuario={datos[1]} iglesias={datos[2]} />
      )}
    </section>
  )
}
