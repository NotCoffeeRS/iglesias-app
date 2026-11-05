import { useEffect, useState } from 'react'
import {
  guardarHoja,
  obtenerHojas,
  SERVICIOS,
  type HojaAsistencia,
  type Servicio,
} from '../../api/asistencia'
import {
  claseBotonPrincipal,
  claseCampo,
  fechaLarga,
  hoyEnMerida,
  mensajeDeError,
  servicioSugerido,
  useCarga,
} from './utilidades'

function Marca({ marcado, modo }: { marcado: boolean; modo: HojaAsistencia['modo'] }) {
  if (!marcado)
    return (
      <span aria-hidden="true" className="h-8 w-8 shrink-0 rounded-full border-2 border-borde" />
    )
  return (
    <span
      aria-hidden="true"
      className={[
        'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
        modo === 'asistencias' ? 'bg-primario text-sobre-primario' : 'bg-peligro text-superficie',
      ].join(' ')}
    >
      <svg
        viewBox="0 0 24 24"
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
      >
        {modo === 'asistencias' ? (
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 12.5l4.5 4.5L19 7.5" />
        ) : (
          <path strokeLinecap="round" d="M7 7l10 10M17 7L7 17" />
        )}
      </svg>
    </span>
  )
}

const idsMarcados = (h: HojaAsistencia) =>
  new Set(h.personas.filter((p) => p.marcado).map((p) => p.miembro_id))

function Hoja({
  hojaInicial,
  fecha,
  servicio,
  onCambios,
  onGuardada,
}: {
  hojaInicial: HojaAsistencia
  fecha: string
  servicio: Servicio
  onCambios: (hay: boolean) => void
  onGuardada: (hoja: HojaAsistencia) => void
}) {
  const [hoja, setHoja] = useState(hojaInicial)
  const [marcados, setMarcados] = useState(() => idsMarcados(hojaInicial))
  const [guardando, setGuardando] = useState(false)
  const [aviso, setAviso] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const base = idsMarcados(hoja)
  const hayCambios = base.size !== marcados.size || [...marcados].some((id) => !base.has(id))
  const asistencias = hoja.modo === 'asistencias'
  const personas = [...hoja.personas].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'))

  // Avisa a la página si hay marcas sin guardar (para preguntar antes de cambiar de lista).
  useEffect(() => {
    onCambios(hayCambios)
  }, [hayCambios, onCambios])

  function alternar(id: number) {
    // Actualización funcional: dos toques rápidos seguidos no se pisan.
    setMarcados((actual) => {
      const nuevos = new Set(actual)
      if (nuevos.has(id)) nuevos.delete(id)
      else nuevos.add(id)
      return nuevos
    })
    setAviso(null)
  }

  function marcarTodos(ids: number[]) {
    setMarcados(new Set(ids))
    setAviso(null)
  }

  async function guardar() {
    setGuardando(true)
    setError(null)
    try {
      const actualizada = await guardarHoja(fecha, servicio, hoja.hoja, [...marcados])
      setHoja(actualizada)
      setMarcados(idsMarcados(actualizada))
      onGuardada(actualizada)
      setAviso('Asistencia guardada.')
    } catch (e) {
      setError(mensajeDeError(e, 'registrar la asistencia de esta lista'))
    } finally {
      setGuardando(false)
    }
  }

  if (personas.length === 0)
    return (
      <p className="rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
        {asistencias
          ? 'Tu célula todavía no tiene integrantes asignados.'
          : 'No hay miembros sin célula en tu iglesia.'}
      </p>
    )

  return (
    <div>
      <p className="text-texto-suave">
        {asistencias ? 'Toca a quien asistió.' : 'Toca a quien faltó.'}
        {hoja.guardada && !hayCambios && ' Ya está registrada; puedes corregirla.'}
      </p>

      <ul className="mt-3 divide-y divide-borde overflow-hidden rounded-3xl border border-borde bg-superficie">
        {personas.map((p) => {
          const marcado = marcados.has(p.miembro_id)
          return (
            <li key={p.miembro_id}>
              <button
                type="button"
                aria-pressed={marcado}
                onClick={() => alternar(p.miembro_id)}
                className={[
                  'flex min-h-16 w-full items-center gap-3 px-4 py-3 text-left text-[1.0625rem] transition-colors',
                  marcado
                    ? asistencias
                      ? 'bg-acento/35'
                      : 'bg-peligro-fondo'
                    : 'hover:bg-superficie-2',
                ].join(' ')}
              >
                <span className={'min-w-0 flex-1 ' + (marcado ? 'font-semibold' : '')}>
                  {p.nombre}
                </span>
                <Marca marcado={marcado} modo={hoja.modo} />
              </button>
            </li>
          )
        })}
      </ul>

      {asistencias && (
        <div className="mt-3 flex gap-2">
          <button
            type="button"
            onClick={() => marcarTodos(personas.map((p) => p.miembro_id))}
            className="rounded-xl px-3 py-2 text-sm font-semibold text-enlace hover:bg-superficie-2"
          >
            Marcar a todos
          </button>
          <button
            type="button"
            onClick={() => marcarTodos([])}
            className="rounded-xl px-3 py-2 text-sm font-semibold text-texto-suave hover:bg-superficie-2"
          >
            Quitar marcas
          </button>
        </div>
      )}

      {/* Barra al alcance del pulgar */}
      <div className="sticky bottom-0 -mx-4 mt-4 border-t border-borde bg-fondo/85 px-4 py-3 backdrop-blur-md md:static md:mx-0 md:border-0 md:bg-transparent md:px-0 md:backdrop-blur-none">
        {error && (
          <p role="alert" className="mb-2 rounded-xl bg-peligro-fondo px-4 py-2.5 text-peligro">
            {error}
          </p>
        )}
        {aviso && (
          <p
            role="status"
            className="mb-2 rounded-xl bg-acento px-4 py-2.5 font-semibold text-acento-texto"
          >
            {aviso}
          </p>
        )}
        <div className="flex items-center gap-3">
          <p className="min-w-0 flex-1 text-sm" aria-live="polite">
            <span className="font-titulo text-2xl font-bold">{marcados.size}</span>
            <span className="text-texto-suave">
              {' '}
              de {personas.length} {asistencias ? 'asistieron' : 'faltaron'}
            </span>
          </p>
          <button
            type="button"
            onClick={guardar}
            disabled={guardando || (!hayCambios && hoja.guardada)}
            className={claseBotonPrincipal}
          >
            {guardando ? 'Guardando…' : hoja.guardada && !hayCambios ? 'Guardada' : 'Guardar'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function PaginaAsistencia() {
  const hoy = hoyEnMerida()
  const [fecha, setFecha] = useState(hoy)
  const [servicio, setServicio] = useState<Servicio>(() => servicioSugerido(hoy))
  const [activa, setActiva] = useState<string | null>(null)
  const [hayCambios, setHayCambios] = useState(false)
  // Hojas guardadas en esta visita, para mostrarlas actualizadas al volver a ellas.
  const [guardadas, setGuardadas] = useState<Record<string, HojaAsistencia>>({})

  const clave = `${fecha}|${servicio}`
  const { estado, reintentar } = useCarga(
    () => obtenerHojas(fecha, servicio),
    'cargar la lista de asistencia',
    clave,
  )

  /** Cambiar de fecha, culto o lista descarta lo no guardado: se pregunta antes. */
  function puedeSalir() {
    return !hayCambios || window.confirm('Tienes marcas sin guardar. ¿Descartarlas?')
  }

  function cambiarFecha(nueva: string) {
    if (!nueva || !puedeSalir()) return
    setFecha(nueva)
    setServicio(servicioSugerido(nueva))
    setHayCambios(false)
  }

  function cambiarServicio(nuevo: Servicio) {
    if (!puedeSalir()) return
    setServicio(nuevo)
    setHayCambios(false)
  }

  const hojas =
    estado.tipo === 'listo' ? estado.datos.map((h) => guardadas[`${clave}|${h.hoja}`] ?? h) : []
  const hoja = hojas.find((h) => h.hoja === activa) ?? hojas[0]

  return (
    <section>
      <h1 className="text-3xl font-bold md:text-4xl">Asistencia</h1>
      <p className="mt-1 text-texto-suave first-letter:uppercase">{fechaLarga(fecha)}</p>

      <div className="mt-5 grid grid-cols-2 gap-3 sm:max-w-lg">
        <label className="block text-sm font-semibold">
          Fecha
          <input
            type="date"
            value={fecha}
            max={hoy}
            onChange={(e) => cambiarFecha(e.target.value)}
            className={claseCampo}
          />
        </label>
        <label className="block text-sm font-semibold">
          Culto
          <select
            value={servicio}
            onChange={(e) => cambiarServicio(e.target.value as Servicio)}
            className={claseCampo}
          >
            {SERVICIOS.map((s) => (
              <option key={s.clave} value={s.clave}>
                {s.nombre}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-5">
        {estado.tipo === 'cargando' && (
          <div className="space-y-2" aria-hidden="true">
            {[0, 1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 animate-pulse rounded-2xl bg-superficie" />
            ))}
          </div>
        )}
        {estado.tipo === 'error' && (
          <div
            role="alert"
            className="rounded-3xl border border-borde bg-superficie p-6 text-center"
          >
            <p className="font-semibold">{estado.mensaje}</p>
            <button type="button" onClick={reintentar} className={claseBotonPrincipal + ' mt-4'}>
              Reintentar
            </button>
          </div>
        )}
        {estado.tipo === 'listo' && hojas.length === 0 && (
          <p className="rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
            No tienes una lista para marcar. La asistencia la registran los líderes de célula y el
            ujier en turno.
          </p>
        )}

        {hojas.length > 1 && (
          <div role="tablist" aria-label="Listas" className="mb-4 flex gap-2">
            {hojas.map((h) => (
              <button
                key={h.hoja}
                type="button"
                role="tab"
                aria-selected={h.hoja === hoja?.hoja}
                onClick={() => {
                  if (h.hoja === hoja?.hoja || !puedeSalir()) return
                  setActiva(h.hoja)
                  setHayCambios(false)
                }}
                className={[
                  'flex-1 rounded-xl px-3 py-2.5 text-sm font-semibold transition-colors',
                  h.hoja === hoja?.hoja
                    ? 'bg-primario text-sobre-primario'
                    : 'border border-borde bg-superficie hover:bg-superficie-2',
                ].join(' ')}
              >
                {h.titulo}
              </button>
            ))}
          </div>
        )}
        {hoja && (
          <>
            {hojas.length === 1 && <h2 className="mb-1 text-xl font-semibold">{hoja.titulo}</h2>}
            <Hoja
              key={`${clave}|${hoja.hoja}`}
              hojaInicial={hoja}
              fecha={fecha}
              servicio={servicio}
              onCambios={setHayCambios}
              onGuardada={(h) => setGuardadas((g) => ({ ...g, [`${clave}|${h.hoja}`]: h }))}
            />
          </>
        )}
      </div>
    </section>
  )
}
