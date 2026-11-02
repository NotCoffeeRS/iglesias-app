import { useState } from 'react'
import {
  DIAS,
  NOMBRES_TIPO,
  type HorarioPublico,
  type IglesiaPublica,
  type SedePublica,
} from '../../api/publico'

/** Solo enlaces http(s); evita que un dato mal capturado se vuelva un enlace peligroso. */
function esEnlaceSeguro(url?: string | null): url is string {
  return !!url && /^https?:\/\//i.test(url)
}

/** "19:30" o "19:30:00" → { hora: "7:30", periodo: "p.m." } */
function partirHora(hora: string): { hora: string; periodo: string } | null {
  const [h, m] = hora.split(':').map(Number)
  if (Number.isNaN(h) || Number.isNaN(m)) return null
  return {
    hora: `${h % 12 || 12}:${String(m).padStart(2, '0')}`,
    periodo: h < 12 ? 'a.m.' : 'p.m.',
  }
}

/** "7:30 p.m.", o "7:30 – 9:00 p.m." si ambas horas son del mismo periodo. */
function rangoHora({ hora_inicio, hora_fin }: HorarioPublico): string {
  const inicio = partirHora(hora_inicio)
  if (!inicio) return hora_inicio
  const fin = hora_fin ? partirHora(hora_fin) : null
  if (!fin) return `${inicio.hora} ${inicio.periodo}`
  return inicio.periodo === fin.periodo
    ? `${inicio.hora} – ${fin.hora} ${fin.periodo}`
    : `${inicio.hora} ${inicio.periodo} – ${fin.hora} ${fin.periodo}`
}

function Horarios({ horarios }: { horarios: HorarioPublico[] }) {
  const porDia = DIAS.map((dia) => ({
    ...dia,
    horarios: horarios
      .filter((h) => h.dia === dia.clave)
      .sort((a, b) => a.hora_inicio.localeCompare(b.hora_inicio)),
  })).filter((dia) => dia.horarios.length > 0)

  if (porDia.length === 0) {
    return <p className="mt-4 text-sm text-texto-suave">Sin horarios publicados.</p>
  }

  return (
    <dl className="mt-4 divide-y divide-borde">
      {porDia.map((dia) => (
        <div key={dia.clave} className="py-3 first:pt-0 last:pb-0">
          <dt className="font-titulo font-semibold text-texto">{dia.nombre}</dt>
          {dia.horarios.map((h) => (
            <dd
              key={h.id}
              className="mt-1 flex items-baseline justify-between gap-3 text-[0.95rem]"
            >
              <span className="min-w-0">
                {NOMBRES_TIPO[h.tipo] ?? h.tipo}
                {h.descripcion && (
                  <span className="block text-sm text-texto-suave">{h.descripcion}</span>
                )}
              </span>
              <span className="shrink-0 whitespace-nowrap text-texto-suave tabular-nums">
                {rangoHora(h)}
              </span>
            </dd>
          ))}
        </div>
      ))}
    </dl>
  )
}

function Sede({ sede, unica }: { sede: SedePublica; unica: boolean }) {
  return (
    <section className="rounded-2xl bg-superficie-2 p-4">
      {!unica && <h3 className="text-lg font-semibold">{sede.nombre}</h3>}
      <p className={unica ? 'text-texto-suave' : 'mt-0.5 text-texto-suave'}>{sede.direccion}</p>
      {esEnlaceSeguro(sede.enlace_maps) && (
        <a
          href={sede.enlace_maps}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex items-center gap-2 rounded-xl bg-primario px-4 py-2.5 text-sm font-semibold text-sobre-primario transition-colors hover:bg-primario-hover"
        >
          <svg
            viewBox="0 0 24 24"
            className="h-4 w-4"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z" />
            <circle cx="12" cy="9.5" r="2.5" />
          </svg>
          Cómo llegar
        </a>
      )}
      <Horarios horarios={sede.horarios} />
    </section>
  )
}

export default function TarjetaIglesia({ iglesia }: { iglesia: IglesiaPublica }) {
  const [fotoRota, setFotoRota] = useState(false)
  const variasSedes = iglesia.sedes.length > 1
  const redes = iglesia.redes.filter((r) => esEnlaceSeguro(r.url))

  return (
    <article
      id={`iglesia-${iglesia.id}`}
      className={[
        'scroll-mt-20 overflow-hidden rounded-3xl border border-borde bg-superficie',
        variasSedes ? 'md:col-span-2' : '',
      ].join(' ')}
    >
      {esEnlaceSeguro(iglesia.foto_url) && !fotoRota && (
        <img
          src={iglesia.foto_url}
          alt={`Fachada de ${iglesia.nombre}`}
          loading="lazy"
          onError={() => setFotoRota(true)}
          className={[
            'w-full bg-superficie-2 object-cover',
            variasSedes ? 'aspect-[21/9]' : 'aspect-video',
          ].join(' ')}
        />
      )}

      <div className="p-5 md:p-6">
        <h2 className="text-2xl font-bold text-primario">{iglesia.nombre}</h2>
        {iglesia.pastor && <p className="mt-1 text-texto-suave">Pastor {iglesia.pastor}</p>}
        {iglesia.telefono_iglesia && (
          <a
            href={`tel:${iglesia.telefono_iglesia.replace(/[^\d+]/g, '')}`}
            className="mt-1 inline-block font-semibold text-enlace underline-offset-4 hover:underline"
          >
            {iglesia.telefono_iglesia}
          </a>
        )}

        {redes.length > 0 && (
          <ul className="mt-3 flex flex-wrap gap-2">
            {redes.map((red) => (
              <li key={red.url}>
                <a
                  href={red.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block rounded-full bg-acento px-3 py-1 text-sm font-semibold text-acento-texto hover:opacity-85"
                >
                  {red.nombre}
                </a>
              </li>
            ))}
          </ul>
        )}

        <div className={['mt-5 grid gap-3', variasSedes ? 'md:grid-cols-2' : ''].join(' ')}>
          {iglesia.sedes.map((sede) => (
            <Sede key={sede.id} sede={sede} unica={!variasSedes} />
          ))}
        </div>
      </div>
    </article>
  )
}
