import { useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import CuentaMenu from './CuentaMenu'
import Icono from './Icono'
import { SECCIONES_MENU, type EntradaMenu } from './tipos'
import { useMenuVisible } from './useMenuVisible'

interface Props {
  menu: EntradaMenu[]
}

function clasesEnlace({ isActive }: { isActive: boolean }) {
  return [
    'flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-[1.0625rem] transition-colors',
    isActive
      ? 'bg-acento font-semibold text-acento-texto'
      : 'text-texto-suave hover:bg-superficie-2 hover:text-texto',
  ].join(' ')
}

function Marca() {
  return (
    <Link to="/" className="block leading-tight">
      <span className="font-titulo text-xl font-bold tracking-tight text-primario">Tessia</span>
      <span className="block text-sm text-texto-suave">Presbiterio de la 3ra IAFCJ</span>
    </Link>
  )
}

/** Estructura común: encabezado, menú (cajón en celular, barra lateral en computadora) y contenido. */
export default function Layout({ menu: menuCompleto }: Props) {
  const menu = useMenuVisible(menuCompleto)
  const ubicacion = useLocation()
  // Las secciones se pueden plegar. Mientras la persona no toque una, se abre sola la que
  // contiene la pantalla donde está.
  const [abiertas, setAbiertas] = useState<Record<string, boolean>>({})
  const [abierto, setAbierto] = useState(false)
  const cerrar = () => setAbierto(false)

  return (
    <div className="min-h-dvh md:flex">
      {/* Encabezado en celular: translúcido, deja ver el contenido al desplazarse */}
      <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-borde/70 bg-fondo/80 px-4 backdrop-blur-md md:hidden">
        <button
          type="button"
          onClick={() => setAbierto(true)}
          aria-label="Abrir menú"
          aria-expanded={abierto}
          className="-ml-2 rounded-xl p-2 text-texto hover:bg-superficie-2"
        >
          <svg
            viewBox="0 0 24 24"
            className="h-6 w-6"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path strokeLinecap="round" d="M4 7h16M4 12h16M4 17h10" />
          </svg>
        </button>
        <Marca />
      </header>

      {/* Velo del cajón en celular */}
      {abierto && (
        <div className="fixed inset-0 z-40 bg-velo md:hidden" onClick={cerrar} aria-hidden="true" />
      )}

      {/* Menú: cajón deslizable en celular, barra fija en computadora */}
      <aside
        className={[
          'fixed inset-y-0 left-0 z-50 flex w-72 max-w-[85vw] flex-col overflow-y-auto bg-superficie transition-transform duration-200',
          'md:sticky md:top-0 md:z-auto md:h-dvh md:w-64 md:shrink-0 md:translate-x-0 md:border-r md:border-borde md:shadow-none',
          abierto ? 'translate-x-0 shadow-2xl' : '-translate-x-full',
        ].join(' ')}
      >
        <div className="flex items-start justify-between px-5 pt-5 pb-4">
          <Marca />
          <button
            type="button"
            onClick={cerrar}
            aria-label="Cerrar menú"
            className="-mr-2 rounded-xl p-2 text-texto-suave hover:bg-superficie-2 md:hidden"
          >
            <svg
              viewBox="0 0 24 24"
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path strokeLinecap="round" d="M6 6l12 12M18 6L6 18" />
            </svg>
          </button>
        </div>
        <nav aria-label="Menú principal" className="flex flex-col gap-1 px-3 pb-6">
          <NavLink to="/" end className={clasesEnlace} onClick={cerrar}>
            <Icono nombre="inicio" />
            Inicio
          </NavLink>
          {SECCIONES_MENU.map(({ clave, titulo }) => {
            const entradas = menu.filter((e) => e.seccion === clave)
            if (entradas.length === 0) return null
            const abierta =
              abiertas[clave] ??
              entradas.some(
                (e) => ubicacion.pathname === e.ruta || ubicacion.pathname.startsWith(e.ruta + '/'),
              )
            return (
              <div key={clave} className="mt-2 border-t border-borde pt-2">
                <button
                  type="button"
                  aria-expanded={abierta}
                  aria-controls={`seccion-${clave}`}
                  onClick={() => setAbiertas((a) => ({ ...a, [clave]: !abierta }))}
                  className="flex w-full items-center justify-between rounded-xl px-3.5 py-2 text-left text-sm font-extrabold tracking-wide text-primario uppercase transition-colors hover:bg-superficie-2"
                >
                  {titulo}
                  <Icono
                    nombre="flecha"
                    className={'h-4 w-4 transition-transform ' + (abierta ? 'rotate-180' : '')}
                  />
                </button>
                {abierta && (
                  <div id={`seccion-${clave}`} className="mt-1 flex flex-col gap-1">
                    {entradas.map((entrada) => (
                      <NavLink
                        key={entrada.ruta}
                        to={entrada.ruta}
                        className={clasesEnlace}
                        onClick={cerrar}
                      >
                        {entrada.icono && <Icono nombre={entrada.icono} />}
                        {entrada.etiqueta}
                      </NavLink>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
          {menu
            .filter((e) => !e.seccion)
            .map((entrada) => (
              <NavLink
                key={entrada.ruta}
                to={entrada.ruta}
                className={clasesEnlace}
                onClick={cerrar}
              >
                {entrada.icono && <Icono nombre={entrada.icono} />}
                {entrada.etiqueta}
              </NavLink>
            ))}
        </nav>
        <CuentaMenu alNavegar={cerrar} />
      </aside>

      <main className="min-w-0 flex-1 px-4 py-6 md:px-10 md:py-10">
        <div className="mx-auto max-w-5xl">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
