import { Link, useLocation, useSearchParams } from 'react-router-dom'
import { listarGrupos, TIPOS_GRUPO, type TipoGrupo } from '../../api/grupos'
import { obtenerYo } from '../../api/usuarios'
import { Cargando, ErrorConReintento } from './comunes'
import { claseBotonPrincipal, nombreTipo, useCarga } from './utilidades'

// Quienes crean grupos (el servidor lo vuelve a validar).
const CARGOS_QUE_CREAN = ['presbitero', 'pastor', 'apoyo_pastor']

export default function ListaGrupos() {
  const ubicacion = useLocation()
  const aviso = (ubicacion.state as { aviso?: string } | null)?.aviso
  const [parametros, setParametros] = useSearchParams()
  const tipo = TIPOS_GRUPO.find((t) => t.clave === parametros.get('tipo'))?.clave as
    TipoGrupo | undefined

  const { estado, reintentar } = useCarga(() => listarGrupos(tipo), 'cargar los grupos', tipo)

  const { estado: sesion } = useCarga(obtenerYo, 'conocer tu cargo')
  const puedeCrear = sesion.tipo === 'listo' && CARGOS_QUE_CREAN.includes(sesion.datos.cargo)

  const grupos =
    estado.tipo === 'listo'
      ? [...estado.datos].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'))
      : []
  const variasIglesias = new Set(grupos.map((g) => g.iglesia_nombre)).size > 1

  const claseFiltro = (activo: boolean) =>
    [
      'block rounded-full px-3.5 py-1.5 text-sm font-semibold whitespace-nowrap transition-colors',
      activo
        ? 'bg-primario text-sobre-primario'
        : 'border border-borde bg-superficie text-texto hover:bg-superficie-2',
    ].join(' ')

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold md:text-4xl">Grupos</h1>
          <p className="mt-1 text-texto-suave">
            Redes, células, ministerios, escuelas y áreas, con su líder.
          </p>
        </div>
        {puedeCrear && (
          <Link to="/grupos/nuevo" className={claseBotonPrincipal}>
            Crear grupo
          </Link>
        )}
      </div>

      {aviso && (
        <p
          role="status"
          className="mt-4 rounded-xl bg-acento px-4 py-2.5 font-semibold text-acento-texto"
        >
          {aviso}
        </p>
      )}

      <nav
        aria-label="Filtrar por tipo"
        className="-mx-4 mt-5 overflow-x-auto px-4 [scrollbar-width:none]"
      >
        <ul className="flex gap-2">
          <li>
            <button
              type="button"
              aria-pressed={!tipo}
              onClick={() => setParametros({}, { replace: true })}
              className={claseFiltro(!tipo)}
            >
              Todos
            </button>
          </li>
          {TIPOS_GRUPO.map((t) => (
            <li key={t.clave}>
              <button
                type="button"
                aria-pressed={tipo === t.clave}
                onClick={() => setParametros({ tipo: t.clave }, { replace: true })}
                className={claseFiltro(tipo === t.clave)}
              >
                {t.plural}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      <div className="mt-5">
        {estado.tipo === 'cargando' && <Cargando />}
        {estado.tipo === 'error' && (
          <ErrorConReintento
            mensaje={estado.mensaje}
            reintentar={estado.sinPermiso ? undefined : reintentar}
          />
        )}
        {estado.tipo === 'listo' && grupos.length === 0 && (
          <p className="rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
            {!puedeCrear
              ? 'No hay grupos en tu área.'
              : tipo
                ? 'No hay grupos de este tipo. Crea el primero.'
                : 'Todavía no hay grupos. Crea el primero.'}
          </p>
        )}
        {grupos.length > 0 && (
          <ul className="grid gap-3 sm:grid-cols-2">
            {grupos.map((g) => (
              <li key={g.id}>
                <Link
                  to={`/grupos/${g.id}/editar`}
                  className="block h-full rounded-3xl border border-borde bg-superficie p-4 transition-colors hover:bg-superficie-2"
                >
                  <span className="flex items-start justify-between gap-3">
                    <span className="font-titulo text-lg font-semibold text-primario">
                      {g.nombre}
                    </span>
                    <span className="shrink-0 rounded-full bg-acento px-2.5 py-0.5 text-xs font-semibold text-acento-texto">
                      {nombreTipo(g.tipo)}
                    </span>
                  </span>
                  {variasIglesias && (
                    <span className="block text-sm text-texto-suave">{g.iglesia_nombre}</span>
                  )}
                  <span className="mt-3 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-sm">
                    <span className="text-texto-suave">Líder</span>
                    <span className="truncate font-semibold">
                      {g.lider_nombre ?? 'Sin asignar'}
                    </span>
                    <span className="text-texto-suave">Asistente</span>
                    <span className="truncate">{g.asistente_nombre ?? 'Sin asignar'}</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
