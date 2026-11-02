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

/** "19:00" o "19:00:00" → "7:00 p. m." */
function formatearHora(hora: string): string {
  const [h, m] = hora.split(':').map(Number)
  if (Number.isNaN(h) || Number.isNaN(m)) return hora
  return new Date(2000, 0, 1, h, m).toLocaleTimeString('es-MX', {
    hour: 'numeric',
    minute: '2-digit',
  })
}

function rangoHora({ hora_inicio, hora_fin }: HorarioPublico): string {
  const inicio = formatearHora(hora_inicio)
  return hora_fin ? `${inicio} – ${formatearHora(hora_fin)}` : inicio
}

function Horarios({ horarios }: { horarios: HorarioPublico[] }) {
  const porDia = DIAS.map((dia) => ({
    ...dia,
    horarios: horarios
      .filter((h) => h.dia === dia.clave)
      .sort((a, b) => a.hora_inicio.localeCompare(b.hora_inicio)),
  })).filter((dia) => dia.horarios.length > 0)

  if (porDia.length === 0) {
    return <p className="text-sm text-slate-500">Sin horarios publicados.</p>
  }

  return (
    <dl className="divide-y divide-slate-100">
      {porDia.map((dia) => (
        <div key={dia.clave} className="py-2.5 first:pt-0 last:pb-0">
          <dt className="text-sm font-semibold text-primario">{dia.nombre}</dt>
          {dia.horarios.map((h) => (
            <dd key={h.id} className="mt-1 flex gap-3 text-sm">
              <span className="w-36 shrink-0 tabular-nums text-slate-700">{rangoHora(h)}</span>
              <span className="min-w-0 text-slate-800">
                {NOMBRES_TIPO[h.tipo] ?? h.tipo}
                {h.descripcion && <span className="block text-slate-500">{h.descripcion}</span>}
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
    <section className="rounded-xl border border-slate-200 p-4">
      {!unica && <h3 className="font-semibold text-slate-800">{sede.nombre}</h3>}
      <p className={unica ? 'text-slate-700' : 'mt-1 text-slate-700'}>{sede.direccion}</p>
      {esEnlaceSeguro(sede.enlace_maps) && (
        <a
          href={sede.enlace_maps}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex items-center gap-2 rounded-lg bg-primario px-4 py-2.5 text-sm font-semibold text-white hover:bg-primario-claro"
        >
          <svg
            viewBox="0 0 24 24"
            className="h-4 w-4"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z" />
            <circle cx="12" cy="9.5" r="2.5" />
          </svg>
          Cómo llegar
        </a>
      )}
      <h4 className="mt-4 mb-2 text-xs font-semibold tracking-wide text-slate-500 uppercase">
        Horarios
      </h4>
      <Horarios horarios={sede.horarios} />
    </section>
  )
}

export default function TarjetaIglesia({ iglesia }: { iglesia: IglesiaPublica }) {
  const [fotoRota, setFotoRota] = useState(false)
  const unicaSede = iglesia.sedes.length === 1

  return (
    <article
      id={`iglesia-${iglesia.id}`}
      className="scroll-mt-20 overflow-hidden rounded-2xl bg-white shadow-sm"
    >
      {esEnlaceSeguro(iglesia.foto_url) && !fotoRota && (
        <img
          src={iglesia.foto_url}
          alt={`Fachada de ${iglesia.nombre}`}
          loading="lazy"
          onError={() => setFotoRota(true)}
          className="aspect-video w-full bg-acento/30 object-cover"
        />
      )}

      <div className="p-4 sm:p-6">
        <h2 className="text-xl font-bold text-primario">{iglesia.nombre}</h2>
        {iglesia.pastor && <p className="mt-1 text-slate-600">Pastor: {iglesia.pastor}</p>}
        {iglesia.telefono_iglesia && (
          <p className="mt-1">
            <a
              href={`tel:${iglesia.telefono_iglesia.replace(/[^\d+]/g, '')}`}
              className="font-medium text-primario-claro underline-offset-2 hover:underline"
            >
              {iglesia.telefono_iglesia}
            </a>
          </p>
        )}

        {iglesia.redes.some((r) => esEnlaceSeguro(r.url)) && (
          <ul className="mt-3 flex flex-wrap gap-2">
            {iglesia.redes
              .filter((r) => esEnlaceSeguro(r.url))
              .map((red) => (
                <li key={red.url}>
                  <a
                    href={red.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block rounded-full bg-acento/40 px-3 py-1 text-sm font-medium text-primario hover:bg-acento/70"
                  >
                    {red.nombre}
                  </a>
                </li>
              ))}
          </ul>
        )}

        <div className="mt-4 space-y-3">
          {iglesia.sedes.map((sede) => (
            <Sede key={sede.id} sede={sede} unica={unicaSede} />
          ))}
        </div>
      </div>
    </article>
  )
}
