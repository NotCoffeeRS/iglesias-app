import { useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import type { EntradaMenu } from './tipos'

interface Props {
  menu: EntradaMenu[]
}

function clasesEnlace({ isActive }: { isActive: boolean }) {
  return [
    'block rounded-lg px-3 py-2.5 text-base font-medium transition-colors',
    isActive ? 'bg-primario text-white' : 'text-slate-700 hover:bg-acento/40',
  ].join(' ')
}

/** Estructura común: encabezado, menú (cajón en celular, barra lateral en computadora) y contenido. */
export default function Layout({ menu }: Props) {
  const [abierto, setAbierto] = useState(false)
  const cerrar = () => setAbierto(false)

  const enlaces = (
    <nav aria-label="Menú principal" className="flex flex-col gap-1 p-3">
      <NavLink to="/" end className={clasesEnlace} onClick={cerrar}>
        Inicio
      </NavLink>
      {menu.map((entrada) => (
        <NavLink key={entrada.ruta} to={entrada.ruta} className={clasesEnlace} onClick={cerrar}>
          {entrada.etiqueta}
        </NavLink>
      ))}
    </nav>
  )

  return (
    <div className="min-h-dvh md:flex">
      {/* Encabezado en celular */}
      <header className="sticky top-0 z-30 flex h-14 items-center gap-3 bg-primario px-4 text-white shadow md:hidden">
        <button
          type="button"
          onClick={() => setAbierto(true)}
          aria-label="Abrir menú"
          aria-expanded={abierto}
          className="-ml-2 rounded-lg p-2 hover:bg-white/10"
        >
          <svg
            viewBox="0 0 24 24"
            className="h-6 w-6"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path strokeLinecap="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <Link to="/" className="truncate text-lg font-semibold">
          Iglesias App
        </Link>
      </header>

      {/* Fondo oscuro del cajón en celular */}
      {abierto && (
        <div
          className="fixed inset-0 z-40 bg-black/40 md:hidden"
          onClick={cerrar}
          aria-hidden="true"
        />
      )}

      {/* Menú: cajón deslizable en celular, barra fija en computadora */}
      <aside
        className={[
          'fixed inset-y-0 left-0 z-50 w-72 max-w-[85vw] overflow-y-auto bg-white transition-transform',
          'md:sticky md:top-0 md:z-auto md:h-dvh md:w-64 md:translate-x-0 md:shadow-none md:border-r md:border-slate-200',
          abierto ? 'translate-x-0 shadow-xl' : '-translate-x-full',
        ].join(' ')}
      >
        <div className="flex h-14 items-center justify-between bg-primario px-4 text-white md:h-16">
          <span className="text-lg font-semibold">Iglesias App</span>
          <button
            type="button"
            onClick={cerrar}
            aria-label="Cerrar menú"
            className="rounded-lg p-2 hover:bg-white/10 md:hidden"
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
        {enlaces}
      </aside>

      <main className="min-w-0 flex-1 px-4 py-5 md:px-8 md:py-8">
        <div className="mx-auto max-w-5xl">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
