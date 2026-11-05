import { Link } from 'react-router-dom'
import { listarIglesias } from '../../api/iglesias'
import { Cargando, ErrorConReintento } from './comunes'
import { esEnlaceSeguro, useCarga } from './utilidades'

/** Inicial de la parte distintiva del nombre: "Iglesia 4ta de Mérida" → "4". */
function inicial(nombre: string): string {
  const distintivo = nombre.replace(/^iglesias?\s+(de\s+)?/i, '').trim() || nombre
  return distintivo.charAt(0).toUpperCase()
}

export default function ListaIglesias() {
  const { estado, reintentar } = useCarga(listarIglesias, 'cargar las iglesias')

  return (
    <section>
      <h1 className="text-3xl font-bold md:text-4xl">Iglesias</h1>
      <p className="mt-1 text-texto-suave">Ficha, sedes y redes de cada iglesia.</p>

      <div className="mt-6">
        {estado.tipo === 'cargando' && <Cargando />}
        {estado.tipo === 'error' && (
          <ErrorConReintento mensaje={estado.mensaje} reintentar={reintentar} />
        )}
        {estado.tipo === 'listo' && estado.datos.length === 0 && (
          <p className="rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
            No tienes iglesias asignadas. Pide al presbítero que te dé acceso.
          </p>
        )}
        {estado.tipo === 'listo' && estado.datos.length > 0 && (
          <ul className="grid gap-3 sm:grid-cols-2">
            {estado.datos.map((iglesia) => (
              <li key={iglesia.id}>
                <Link
                  to={`/iglesias/${iglesia.id}`}
                  className="flex h-full items-center gap-4 rounded-3xl border border-borde bg-superficie p-4 transition-colors hover:bg-resalte"
                >
                  {esEnlaceSeguro(iglesia.foto_url) ? (
                    <img
                      src={iglesia.foto_url}
                      alt=""
                      loading="lazy"
                      className="h-16 w-16 shrink-0 rounded-2xl bg-superficie-2 object-cover"
                    />
                  ) : (
                    <span
                      aria-hidden="true"
                      className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-acento font-titulo text-2xl font-bold text-acento-texto"
                    >
                      {inicial(iglesia.nombre)}
                    </span>
                  )}
                  <span className="min-w-0">
                    <span className="block font-titulo text-lg font-semibold text-primario">
                      {iglesia.nombre}
                    </span>
                    {iglesia.pastor && (
                      <span className="block truncate text-sm text-texto-suave">
                        Pastor {iglesia.pastor}
                      </span>
                    )}
                    <span className="block text-sm text-texto-suave">
                      {iglesia.total_sedes === 1 ? '1 sede' : `${iglesia.total_sedes} sedes`}
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
