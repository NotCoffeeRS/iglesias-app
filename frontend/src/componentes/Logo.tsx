/**
 * Logo de Tessia. `simbolo` es solo la figura, `letras` solo el nombre y `completo` los dos juntos.
 * En modo oscuro se usa la versión con colores aclarados (el logo original es de fondo claro).
 */
export default function Logo({
  tipo = 'simbolo',
  alt = '',
  className = '',
}: {
  tipo?: 'simbolo' | 'letras' | 'completo'
  /** Texto alternativo; vacío cuando el nombre ya está escrito al lado. */
  alt?: string
  className?: string
}) {
  const base = { simbolo: '/tessia-simbolo', letras: '/tessia-letras', completo: '/tessia-logo' }[
    tipo
  ]
  return (
    <picture>
      <source media="(prefers-color-scheme: dark)" srcSet={`${base}-oscuro.svg`} />
      <img src={`${base}.svg`} alt={alt} className={className} />
    </picture>
  )
}
