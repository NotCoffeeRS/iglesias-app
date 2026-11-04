import { useMemo, useState } from 'react'
import { Link, useLocation, useSearchParams } from 'react-router-dom'
import { ESTADOS, listarMiembros, type EstadoMiembro } from '../../api/miembros'
import { Cargando, ErrorConReintento, EtiquetaEstado } from './comunes'
import { claseBotonPrincipal, claseCampo, normalizar, useCarga } from './utilidades'

export default function ListaMiembros() {
  const ubicacion = useLocation()
  const aviso = (ubicacion.state as { aviso?: string } | null)?.aviso
  // El estado sí puede ir en la URL (no es dato personal); la búsqueda por nombre no.
  const [parametros, setParametros] = useSearchParams()
  const estado = (ESTADOS.find((e) => e.clave === parametros.get('estado'))?.clave ?? undefined) as
    EstadoMiembro | undefined
  const [busqueda, setBusqueda] = useState('')

  const { estado: carga, reintentar } = useCarga(
    () => listarMiembros(estado),
    'cargar los miembros',
    estado,
  )

  const visibles = useMemo(() => {
    if (carga.tipo !== 'listo') return []
    const texto = normalizar(busqueda)
    const lista = texto
      ? carga.datos.filter((m) => normalizar(m.nombre).includes(texto))
      : carga.datos
    return [...lista].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'))
  }, [carga, busqueda])

  const variasIglesias =
    carga.tipo === 'listo' && new Set(carga.datos.map((m) => m.iglesia_nombre)).size > 1

  function elegirEstado(clave?: EstadoMiembro) {
    setParametros(clave ? { estado: clave } : {}, { replace: true })
  }

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
          <h1 className="text-3xl font-bold md:text-4xl">Miembros</h1>
          {carga.tipo === 'listo' && (
            <p className="mt-1 text-texto-suave">
              {carga.datos.length === 1 ? '1 persona' : `${carga.datos.length} personas`}
              {estado ? ' con este estado' : ''}
            </p>
          )}
        </div>
        <Link to="/miembros/nuevo" className={claseBotonPrincipal}>
          Registrar miembro
        </Link>
      </div>

      {aviso && (
        <p
          role="status"
          className="mt-4 rounded-xl bg-acento px-4 py-2.5 font-semibold text-acento-texto"
        >
          {aviso}
        </p>
      )}

      <label className="mt-5 block max-w-md text-sm font-semibold">
        Buscar por nombre
        <input
          type="search"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          autoComplete="off"
          className={claseCampo}
        />
      </label>

      <nav
        aria-label="Filtrar por estado"
        className="-mx-4 mt-4 overflow-x-auto px-4 [scrollbar-width:none]"
      >
        <ul className="flex gap-2">
          <li>
            <button
              type="button"
              aria-pressed={!estado}
              onClick={() => elegirEstado()}
              className={claseFiltro(!estado)}
            >
              Todos
            </button>
          </li>
          {ESTADOS.map((e) => (
            <li key={e.clave}>
              <button
                type="button"
                aria-pressed={estado === e.clave}
                onClick={() => elegirEstado(e.clave)}
                className={claseFiltro(estado === e.clave)}
              >
                {e.nombre}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      <div className="mt-5">
        {carga.tipo === 'cargando' && <Cargando />}
        {carga.tipo === 'error' && (
          <ErrorConReintento mensaje={carga.mensaje} reintentar={reintentar} />
        )}
        {carga.tipo === 'listo' && visibles.length === 0 && (
          <p className="rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
            {busqueda
              ? `Nadie coincide con “${busqueda.trim()}”. Revisa cómo se escribe el nombre.`
              : estado
                ? 'No hay miembros con este estado.'
                : 'Todavía no hay miembros registrados. Registra el primero.'}
          </p>
        )}
        {carga.tipo === 'listo' && visibles.length > 0 && (
          <ul className="divide-y divide-borde overflow-hidden rounded-3xl border border-borde bg-superficie">
            {visibles.map((m) => (
              <li key={m.id}>
                <Link
                  to={`/miembros/${m.id}/editar`}
                  className="block px-4 py-3.5 transition-colors hover:bg-superficie-2"
                >
                  <span className="block truncate font-semibold">{m.nombre}</span>
                  <span className="mt-1 flex items-center gap-2 text-sm text-texto-suave">
                    <EtiquetaEstado estado={m.estado} />
                    <span className="min-w-0 truncate">
                      {[m.telefono, variasIglesias ? m.iglesia_nombre : null]
                        .filter(Boolean)
                        .join(', ') || 'Sin teléfono'}
                    </span>
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
