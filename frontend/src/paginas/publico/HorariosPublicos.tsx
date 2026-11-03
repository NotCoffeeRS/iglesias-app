import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { obtenerIglesiasPublicas, type IglesiaPublica } from '../../api/publico'
import TarjetaIglesia from './TarjetaIglesia'

type Estado =
  { tipo: 'cargando' } | { tipo: 'error' } | { tipo: 'listo'; iglesias: IglesiaPublica[] }

function Esqueleto() {
  return (
    <div className="grid gap-4 md:grid-cols-2" aria-hidden="true">
      {[0, 1].map((i) => (
        <div key={i} className="animate-pulse rounded-3xl border border-borde bg-superficie p-6">
          <div className="h-7 w-2/3 rounded-lg bg-superficie-2" />
          <div className="mt-3 h-4 w-1/2 rounded bg-superficie-2" />
          <div className="mt-6 h-28 rounded-2xl bg-superficie-2" />
        </div>
      ))}
    </div>
  )
}

/** Título con tipografía cinética: se ensancha y gana peso una sola vez al cargar. */
function TituloCinetico() {
  const titulo = useRef<HTMLHeadingElement>(null)

  useEffect(() => {
    const reducir = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reducir || !titulo.current?.animate) return
    titulo.current.animate(
      [
        { fontStretch: '75%', fontWeight: 500, opacity: 0.4 },
        { fontStretch: '100%', fontWeight: 800, opacity: 1 },
      ],
      { duration: 900, easing: 'cubic-bezier(0.2, 0.7, 0.2, 1)' },
    )
  }, [])

  return (
    <h1
      ref={titulo}
      className="text-[2.75rem] leading-[0.95] font-extrabold tracking-tight text-primario md:text-7xl"
    >
      Horarios y ubicaciones
    </h1>
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
      <header className="sticky top-0 z-30 border-b border-borde/70 bg-fondo/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between gap-4 px-4">
          <span className="font-titulo text-xl font-bold tracking-tight text-primario">
            Iglesias
          </span>
          <Link
            to="/login"
            className="rounded-xl px-3 py-2 text-sm font-semibold text-enlace hover:bg-superficie-2"
          >
            Iniciar sesión
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 pt-8 pb-12 md:pt-14">
        <TituloCinetico />
        <p className="mt-4 max-w-prose text-lg text-texto-suave">
          Las iglesias del Presbiterio de la 3ra IAFCJ: cuándo nos reunimos y cómo llegar.
        </p>

        <div className="mt-8">
          {estado.tipo === 'cargando' && <Esqueleto />}

          {estado.tipo === 'error' && (
            <div
              role="alert"
              className="rounded-3xl border border-borde bg-superficie p-6 text-center"
            >
              <p className="font-semibold">No se pudieron cargar los horarios.</p>
              <p className="mt-1 text-texto-suave">Revisa tu conexión e inténtalo otra vez.</p>
              <button
                type="button"
                onClick={reintentar}
                className="mt-4 rounded-xl bg-primario px-5 py-2.5 font-semibold text-sobre-primario hover:bg-primario-hover"
              >
                Reintentar
              </button>
            </div>
          )}

          {estado.tipo === 'listo' && estado.iglesias.length === 0 && (
            <p className="rounded-3xl border border-borde bg-superficie p-6 text-center text-texto-suave">
              Todavía no hay iglesias publicadas.
            </p>
          )}

          {estado.tipo === 'listo' && estado.iglesias.length > 0 && (
            <>
              {estado.iglesias.length > 1 && (
                <nav
                  aria-label="Ir a una iglesia"
                  className="-mx-4 mb-5 overflow-x-auto px-4 [scrollbar-width:none]"
                >
                  <ul className="flex gap-2">
                    {estado.iglesias.map((iglesia) => (
                      <li key={iglesia.id} className="shrink-0">
                        <a
                          href={`#iglesia-${iglesia.id}`}
                          className="block rounded-full border border-borde bg-superficie px-4 py-2 text-sm font-semibold text-texto hover:bg-acento hover:text-acento-texto"
                        >
                          {iglesia.nombre}
                        </a>
                      </li>
                    ))}
                  </ul>
                </nav>
              )}
              {/* Mosaico: la iglesia con varias sedes ocupa todo el ancho */}
              <div className="grid gap-4 md:grid-cols-2 md:gap-5">
                {estado.iglesias.map((iglesia) => (
                  <TarjetaIglesia key={iglesia.id} iglesia={iglesia} />
                ))}
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  )
}
