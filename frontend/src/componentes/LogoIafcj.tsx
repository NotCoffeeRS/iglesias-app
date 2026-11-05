/**
 * Escudo de la IAFCJ. El archivo tiene fondo transparente y un borde claro alrededor del escudo,
 * por eso se ve bien en modo claro y en oscuro. Mide 353 × 480: la proporción no se toca.
 */
export default function LogoIafcj({ className = '' }: { className?: string }) {
  return (
    <img
      src="/logo-iafcj.png"
      width={353}
      height={480}
      alt="Logo de la IAFCJ"
      className={className}
    />
  )
}
