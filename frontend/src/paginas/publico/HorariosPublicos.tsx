import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { obtenerIglesiasPublicas, type IglesiaPublica } from '../../api/publico'
import TarjetaIglesia from './TarjetaIglesia'

type Estado =
  { tipo: 'cargando' } | { tipo: 'error' } | { tipo: 'listo'; iglesias: IglesiaPublica[] }

function Esqueleto() {
  return (
    <div className="space-y-4" aria-hidden="true">
      {[0, 1].map((i) => (
        <div key={i} className="animate-pulse rounded-2xl bg-white p-6 shadow-sm">
          <div className="h-6 w-2/3 rounded bg-slate-200" />
          <div className="mt-3 h-4 w-1/2 rounded bg-slate-200" />
          <div className="mt-6 h-24 rounded-xl bg-slate-100" />
        </div>
      ))}
    </div>
  )
}

/** Página pública (sin sesión): iglesias, sedes, horarios y cómo llegar. */
export default function HorariosPublicos() {
  const [estado, setEstado] = useState<Estado>({ tipo: 'cargando' })
  const [intento, setIntento] = useState(0)

  useEffect(() => {
    let vigente = true
    obtenerIglesiasPublicas()
      .then((iglesias) => vigente && setEstado({ tipo: 'listo', iglesias }))
      .catch(() => vigente && setEstado({ tipo: 'error' }))
    return () => {
      vigente = false
    }
  }, [intento])

  function reintentar() {
    setEstado({ tipo: 'cargando' })
    setIntento((n) => n + 1)
  }

  return (
    <div className="min-h-dvh bg-fondo">
      <header className="bg-primario text-white">
        <div className="mx-auto flex max-w-3xl items-start justify-between gap-4 px-4 pt-5 pb-6">
          <div>
            <p className="text-sm text-acento">Presbiterio de la 3ra IAFCJ</p>
            <h1 className="mt-1 text-2xl font-bold">Horarios y ubicaciones</h1>
          </div>
          <Link
            to="/login"
            className="shrink-0 rounded-lg border border-white/40 px-3 py-1.5 text-sm font-medium hover:bg-white/10"
          >
            Iniciar sesión
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-5">
        {estado.tipo === 'cargando' && <Esqueleto />}

        {estado.tipo === 'error' && (
          <div role="alert" className="rounded-2xl bg-white p-6 text-center shadow-sm">
            <p className="text-slate-700">No se pudieron cargar los horarios.</p>
            <button
              type="button"
              onClick={reintentar}
              className="mt-4 rounded-lg bg-primario px-5 py-2.5 font-medium text-white hover:bg-primario-claro"
            >
              Reintentar
            </button>
          </div>
        )}

        {estado.tipo === 'listo' && estado.iglesias.length === 0 && (
          <p className="rounded-2xl bg-white p-6 text-center text-slate-600 shadow-sm">
            Todavía no hay iglesias publicadas.
          </p>
        )}

        {estado.tipo === 'listo' && estado.iglesias.length > 0 && (
          <>
            {estado.iglesias.length > 1 && (
              <nav aria-label="Ir a una iglesia" className="-mx-4 mb-4 overflow-x-auto px-4">
                <ul className="flex gap-2">
                  {estado.iglesias.map((iglesia) => (
                    <li key={iglesia.id} className="shrink-0">
                      <a
                        href={`#iglesia-${iglesia.id}`}
                        className="block rounded-full border border-primario/20 bg-white px-3 py-1.5 text-sm font-medium text-primario hover:bg-acento/40"
                      >
                        {iglesia.nombre}
                      </a>
                    </li>
                  ))}
                </ul>
              </nav>
            )}
            <div className="space-y-5">
              {estado.iglesias.map((iglesia) => (
                <TarjetaIglesia key={iglesia.id} iglesia={iglesia} />
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  )
}
