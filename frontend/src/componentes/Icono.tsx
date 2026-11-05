import { ICONOS, type NombreIcono } from './iconos'

/** Ícono de línea decorativo: el texto que lo acompaña es el que se lee (aria-hidden). */
export default function Icono({
  nombre,
  className = 'h-5 w-5',
}: {
  nombre: NombreIcono
  className?: string
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {ICONOS[nombre].map((trazo) => (
        <path key={trazo} d={trazo} />
      ))}
    </svg>
  )
}
