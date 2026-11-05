import { Link } from 'react-router-dom'
import type { EntradaMenu } from './tipos'
import { useMenuVisible } from './useMenuVisible'

function fechaDeHoy(): string {
  const texto = new Date().toLocaleDateString('es-MX', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    timeZone: 'America/Merida',
  })
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

/**
 * Pantalla por defecto de `/`: mosaico (bento) con los módulos que traen `descripcion` en su menú.
 * El primero ocupa el bloque grande.
 */
export default function Inicio({ menu }: { menu: EntradaMenu[] }) {
  const visibles = useMenuVisible(menu)
  const accesos = visibles.filter((e) => e.descripcion)

  return (
    <section>
      <p className="text-texto-suave">{fechaDeHoy()}</p>
      <h1 className="mt-1 text-3xl font-bold md:text-4xl">Inicio</h1>

      {accesos.length === 0 ? (
        <p className="mt-6 max-w-prose rounded-2xl border border-borde bg-superficie p-6 text-texto-suave">
          Aquí aparecerán los accesos a cada módulo (miembros, asistencia, ingresos, gastos…)
          conforme se vayan agregando.
        </p>
      ) : (
        <ul className="mt-6 grid auto-rows-[minmax(8.5rem,auto)] grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
          {accesos.map((acceso, i) => (
            <li key={acceso.ruta} className={i === 0 ? 'col-span-2 md:row-span-2' : ''}>
              <Link
                to={acceso.ruta}
                className={[
                  'flex h-full flex-col justify-end rounded-3xl p-5 transition-colors',
                  i === 0
                    ? 'bg-primario text-sobre-primario hover:bg-primario-hover'
                    : 'border border-borde bg-superficie hover:bg-superficie-2',
                ].join(' ')}
              >
                <span
                  className={
                    i === 0
                      ? 'font-titulo text-3xl font-bold'
                      : 'font-titulo text-xl font-semibold text-primario'
                  }
                >
                  {acceso.etiqueta}
                </span>
                <span
                  className={
                    i === 0 ? 'mt-1 opacity-85' : 'mt-1 text-sm leading-snug text-texto-suave'
                  }
                >
                  {acceso.descripcion}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
