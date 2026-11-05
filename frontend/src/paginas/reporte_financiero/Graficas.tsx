import type { Partida, Resumen } from '../../api/reporte_financiero'
import { aCentavos, formatearMonto, prepararPartidas } from './utilidades'

function IconoBalance({ balance }: { balance: number }) {
  // El signo nunca depende solo del color: lleva icono y una frase.
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-5 w-5 shrink-0"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      aria-hidden="true"
    >
      {balance > 0 && (
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 19V5M5 12l7-7 7 7" />
      )}
      {balance < 0 && (
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 5v14M5 12l7 7 7-7" />
      )}
      {balance === 0 && <path strokeLinecap="round" d="M5 9h14M5 15h14" />}
    </svg>
  )
}

function fraseBalance(balance: number, ingresos: number, gastos: number): string {
  if (ingresos === 0 && gastos === 0) return 'Sin ingresos ni gastos en este periodo.'
  if (balance > 0) return 'Ingresó más de lo que se gastó.'
  if (balance < 0) return 'Se gastó más de lo que ingresó.'
  return 'Los ingresos y los gastos quedaron iguales.'
}

/** El número principal de la vista (balance) y, debajo, los dos que lo forman. */
export function Cifras({ resumen, titulo }: { resumen: Resumen; titulo: string }) {
  const ingresos = aCentavos(resumen.ingresos) ?? 0
  const gastos = aCentavos(resumen.gastos) ?? 0
  const balance = (resumen.balance != null ? aCentavos(resumen.balance) : null) ?? ingresos - gastos

  return (
    <section aria-label={titulo} className="rounded-3xl border border-borde bg-superficie p-5">
      <p className="text-sm text-texto-suave">{titulo}</p>
      <p className="mt-1 text-5xl font-bold tracking-tight break-words">
        {formatearMonto(balance)}
      </p>
      <p
        className={
          'mt-2 flex items-center gap-2 text-sm font-semibold ' +
          (balance < 0 ? 'text-peligro' : 'text-texto-suave')
        }
      >
        <IconoBalance balance={balance} />
        {fraseBalance(balance, ingresos, gastos)}
      </p>
      {/* En celular, una cifra debajo de la otra (así ninguna se parte); desde sm, lado a lado. */}
      <dl className="mt-5 grid gap-3 sm:grid-cols-2">
        <div className="flex items-baseline justify-between gap-3 rounded-2xl bg-superficie-2 p-4 sm:block">
          <dt className="text-sm text-texto-suave">Ingresos</dt>
          <dd className="text-2xl font-semibold whitespace-nowrap sm:mt-1">
            {formatearMonto(ingresos)}
          </dd>
        </div>
        <div className="flex items-baseline justify-between gap-3 rounded-2xl bg-superficie-2 p-4 sm:block">
          <dt className="text-sm text-texto-suave">Gastos</dt>
          <dd className="text-2xl font-semibold whitespace-nowrap sm:mt-1">
            {formatearMonto(gastos)}
          </dd>
        </div>
      </dl>
    </section>
  )
}

/**
 * Barras horizontales de UNA sola serie: un color, el nombre y el monto en texto (que también es la
 * "tabla" para lectores de pantalla) y la barra solo como apoyo visual.
 */
export function Barras({
  titulo,
  partidas,
  vacio,
}: {
  titulo: string
  partidas: Partida[]
  vacio: string
}) {
  const items = prepararPartidas(partidas)
  const maximo = Math.max(...items.map((i) => i.centavos), 1)

  return (
    <section className="rounded-3xl border border-borde bg-superficie p-5">
      <h2 className="text-lg font-semibold">{titulo}</h2>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-texto-suave">{vacio}</p>
      ) : (
        <ul className="mt-4 space-y-4">
          {items.map((i) => (
            <li key={i.clave}>
              <div className="flex items-baseline justify-between gap-3">
                <span className="min-w-0">{i.nombre}</span>
                <span className="shrink-0 font-semibold">{formatearMonto(i.centavos)}</span>
              </div>
              <div className="mt-1.5 border-l border-borde" aria-hidden="true">
                <div
                  className="h-3 rounded-r-[4px] bg-primario"
                  style={{ width: `${Math.max(2, (i.centavos / maximo) * 100)}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
