import { useState, type FormEvent, type ReactNode } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  actualizarMenor,
  crearMenor,
  listarIglesias,
  obtenerMenor,
  type Menor,
  type MenorEntrada,
  type Sexo,
  type Tutor,
} from '../../api/menores'
import { obtenerYo } from '../../api/usuarios'
import {
  claseBotonPrincipal,
  claseBotonSecundario,
  claseCampo,
  hoyEnMerida,
} from '../miembros/utilidades'
import { CATEGORIAS, esGestor, mensaje, useCarga } from './utilidades'

function Campo({ texto, children }: { texto: string; children: ReactNode }) {
  return (
    <label className="block text-sm font-semibold">
      <span>{texto}</span>
      {children}
    </label>
  )
}

function Editor({
  inicial,
  iglesias,
}: {
  inicial: Menor | null
  iglesias: { id: number; nombre: string }[]
}) {
  const navegar = useNavigate()
  const [nombre, setNombre] = useState(inicial?.nombre ?? '')
  const [iglesia, setIglesia] = useState(
    inicial ? String(inicial.iglesia_id) : iglesias.length === 1 ? String(iglesias[0].id) : '',
  )
  const [nacimiento, setNacimiento] = useState(inicial?.fecha_nacimiento ?? '')
  const [sexo, setSexo] = useState<Sexo | ''>(inicial?.sexo ?? '')
  const [direccion, setDireccion] = useState(inicial?.direccion ?? '')
  const [activo, setActivo] = useState(inicial?.activo ?? true)
  const [tutores, setTutores] = useState<Tutor[]>(
    inicial?.tutores ?? [{ nombre: '', telefono: '' }],
  )
  const [error, setError] = useState('')
  const [guardando, setGuardando] = useState(false)
  const hoy = hoyEnMerida()
  const edad = nacimiento
    ? Number(hoy.slice(0, 4)) -
      Number(nacimiento.slice(0, 4)) -
      (hoy.slice(5) < nacimiento.slice(5) ? 1 : 0)
    : null
  const categoria =
    edad !== null && sexo && edad >= 4 && edad <= 17
      ? edad >= 12
        ? 'adolescente'
        : sexo === 'femenino'
          ? 'nina'
          : 'nino'
      : null

  function cambiarTutor(indice: number, campo: keyof Tutor, valor: string) {
    setTutores((lista) => lista.map((t, i) => (i === indice ? { ...t, [campo]: valor } : t)))
  }
  async function guardar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    if (guardando) return
    setError('')
    if (!nombre.trim() || !iglesia || !sexo || !direccion.trim()) {
      setError('Completa nombre, iglesia, sexo y dirección.')
      return
    }
    if (edad === null || edad < 4 || edad > 17) {
      setError('La edad debe estar entre 4 y 17 años cumplidos.')
      return
    }
    if (tutores.length === 0 || tutores.some((t) => !t.nombre.trim() || !t.telefono.trim())) {
      setError('Cada tutor necesita nombre y teléfono. Debe haber al menos uno.')
      return
    }
    const datos: MenorEntrada = {
      iglesia_id: Number(iglesia),
      nombre: nombre.trim(),
      fecha_nacimiento: nacimiento,
      sexo,
      direccion: direccion.trim(),
      activo,
      tutores: tutores.map((t) => ({ nombre: t.nombre.trim(), telefono: t.telefono.trim() })),
    }
    setGuardando(true)
    try {
      if (inicial) await actualizarMenor(inicial.id, datos)
      else await crearMenor(datos)
      navegar('/menores', { replace: true, state: { guardado: true } })
    } catch (e) {
      setError(mensaje(e))
      setGuardando(false)
    }
  }

  return (
    <section className="mx-auto max-w-3xl space-y-5">
      <h1 className="text-3xl font-bold">{inicial ? 'Editar registro' : 'Registrar menor'}</h1>
      <p className="text-texto-suave">
        La categoría se calcula por nacimiento y sexo. No se captura a mano.
      </p>
      <form onSubmit={guardar} noValidate className="space-y-6">
        {error && (
          <p role="alert" className="rounded-xl bg-peligro-fondo p-4 text-peligro">
            {error}
          </p>
        )}
        <fieldset
          disabled={guardando}
          className="grid gap-4 rounded-2xl border border-borde bg-superficie p-5 sm:grid-cols-2"
        >
          <legend className="px-2 font-semibold">Datos del menor</legend>
          <Campo texto="Nombre completo">
            <input
              className={claseCampo}
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              maxLength={150}
              required
              autoComplete="off"
            />
          </Campo>
          <Campo texto="Iglesia">
            <select
              className={claseCampo}
              value={iglesia}
              onChange={(e) => setIglesia(e.target.value)}
              required
            >
              <option value="">Elige la iglesia</option>
              {iglesias.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.nombre}
                </option>
              ))}
            </select>
          </Campo>
          <Campo texto="Fecha de nacimiento">
            <input
              className={claseCampo}
              type="date"
              value={nacimiento}
              onChange={(e) => setNacimiento(e.target.value)}
              max={hoy}
              required
            />
          </Campo>
          <Campo texto="Sexo">
            <select
              className={claseCampo}
              value={sexo}
              onChange={(e) => setSexo(e.target.value as Sexo | '')}
              required
            >
              <option value="">Elige una opción</option>
              <option value="femenino">Femenino</option>
              <option value="masculino">Masculino</option>
            </select>
          </Campo>
          <p className="sm:col-span-2" aria-live="polite">
            {categoria
              ? `${CATEGORIAS[categoria]} · ${edad} años`
              : 'Edad permitida: de 4 a 17 años.'}
          </p>
          <div className="sm:col-span-2">
            <Campo texto="Dirección">
              <textarea
                className={claseCampo}
                value={direccion}
                onChange={(e) => setDireccion(e.target.value)}
                required
                rows={2}
                autoComplete="off"
              />
            </Campo>
          </div>
          {inicial && (
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={activo}
                onChange={(e) => setActivo(e.target.checked)}
              />
              Registro activo
            </label>
          )}
        </fieldset>
        <fieldset
          disabled={guardando}
          className="space-y-4 rounded-2xl border border-borde bg-superficie p-5"
        >
          <legend className="px-2 font-semibold">Tutores</legend>
          <p className="text-sm text-texto-suave">
            Agrega al menos un tutor con nombre y teléfono.
          </p>
          {tutores.map((t, i) => (
            <fieldset
              key={i}
              className="grid gap-3 rounded-xl border border-borde p-4 sm:grid-cols-2"
            >
              <legend className="px-2 text-sm font-semibold">Tutor {i + 1}</legend>
              <Campo texto={`Nombre del tutor ${i + 1}`}>
                <input
                  className={claseCampo}
                  value={t.nombre}
                  onChange={(e) => cambiarTutor(i, 'nombre', e.target.value)}
                  maxLength={150}
                  required
                  autoComplete="off"
                />
              </Campo>
              <Campo texto={`Teléfono del tutor ${i + 1}`}>
                <input
                  className={claseCampo}
                  type="tel"
                  value={t.telefono}
                  onChange={(e) => cambiarTutor(i, 'telefono', e.target.value)}
                  maxLength={20}
                  required
                  autoComplete="off"
                />
              </Campo>
              <button
                className={claseBotonSecundario}
                type="button"
                disabled={tutores.length === 1}
                onClick={() => setTutores((lista) => lista.filter((_, n) => n !== i))}
              >
                Quitar tutor {i + 1}
              </button>
            </fieldset>
          ))}
          <button
            className={claseBotonSecundario}
            type="button"
            onClick={() => setTutores((lista) => [...lista, { nombre: '', telefono: '' }])}
          >
            Agregar tutor
          </button>
        </fieldset>
        <div className="flex flex-wrap gap-3">
          <button className={claseBotonPrincipal} type="submit" disabled={guardando}>
            {guardando ? 'Guardando…' : 'Guardar registro'}
          </button>
          <button
            className={claseBotonSecundario}
            type="button"
            disabled={guardando}
            onClick={() => navegar('/menores')}
          >
            Cancelar
          </button>
        </div>
      </form>
    </section>
  )
}

export default function FormularioMenor() {
  const { id } = useParams()
  const { estado, reintentar } = useCarga(async () => {
    const yo = await obtenerYo()
    if (!esGestor(yo.cargo)) return null
    const [iglesias, inicial] = await Promise.all([
      listarIglesias(),
      id ? obtenerMenor(Number(id)) : Promise.resolve(null),
    ])
    return { iglesias, inicial }
  }, id)
  if (estado.tipo === 'cargando') return <p role="status">Cargando registro…</p>
  if (estado.tipo === 'error')
    return (
      <div role="alert">
        <p>{estado.mensaje}</p>
        <button className={claseBotonSecundario} onClick={reintentar}>
          Reintentar
        </button>
      </div>
    )
  if (estado.datos === null) return <p role="alert">No tienes permiso para gestionar menores.</p>
  return <Editor key={id ?? 'nuevo'} {...estado.datos} />
}
