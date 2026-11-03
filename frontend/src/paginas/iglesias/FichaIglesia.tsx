import { useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { obtenerIglesia, type RedSocial } from '../../api/iglesias'
import { Cargando, claseBotonPrincipal, ErrorConReintento, Volver } from './comunes'
import { esEnlaceSeguro, useCarga } from './utilidades'

function Telefono({ etiqueta, numero }: { etiqueta: string; numero?: string | null }) {
  if (!numero) return null
  return (
    <p>
      <span className="text-texto-suave">{etiqueta}: </span>
      <a
        href={`tel:${numero.replace(/[^\d+]/g, '')}`}
        className="font-semibold text-enlace underline-offset-4 hover:underline"
      >
        {numero}
      </a>
    </p>
  )
}

function Redes({ titulo, redes }: { titulo: string; redes: RedSocial[] }) {
  const seguras = redes.filter((r) => esEnlaceSeguro(r.url))
  if (seguras.length === 0) return null
  return (
    <div className="mt-4">
      <h3 className="text-sm font-semibold text-texto-suave">{titulo}</h3>
      <ul className="mt-2 flex flex-wrap gap-2">
        {seguras.map((red) => (
          <li key={red.id ?? red.url}>
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
    </div>
  )
}

export default function FichaIglesia() {
  const { id } = useParams()
  const ubicacion = useLocation()
  const guardada = (ubicacion.state as { guardada?: boolean } | null)?.guardada
  const [fotoRota, setFotoRota] = useState(false)
  const { estado, reintentar } = useCarga(() => obtenerIglesia(Number(id)), 'cargar la iglesia', id)

  return (
    <section>
      <Volver a="/iglesias">Iglesias</Volver>

      {guardada && (
        <p
          role="status"
          className="mt-3 rounded-xl bg-acento px-4 py-2.5 font-semibold text-acento-texto"
        >
          Cambios guardados.
        </p>
      )}

      <div className="mt-3">
        {estado.tipo === 'cargando' && <Cargando />}
        {estado.tipo === 'error' && (
          <ErrorConReintento mensaje={estado.mensaje} reintentar={reintentar} />
        )}
        {estado.tipo === 'listo' && (
          <article className="overflow-hidden rounded-3xl border border-borde bg-superficie">
            {esEnlaceSeguro(estado.datos.foto_url) && !fotoRota && (
              <img
                src={estado.datos.foto_url}
                alt={`Fachada de ${estado.datos.nombre}`}
                onError={() => setFotoRota(true)}
                className="aspect-[21/9] w-full bg-superficie-2 object-cover"
              />
            )}
            <div className="p-5 md:p-6">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h1 className="text-3xl font-bold text-primario">{estado.datos.nombre}</h1>
                  {estado.datos.pastor && (
                    <p className="mt-1 text-texto-suave">Pastor {estado.datos.pastor}</p>
                  )}
                </div>
                <Link to={`/iglesias/${estado.datos.id}/editar`} className={claseBotonPrincipal}>
                  Editar ficha
                </Link>
              </div>

              <div className="mt-4 space-y-1">
                <Telefono etiqueta="Iglesia" numero={estado.datos.telefono_iglesia} />
                <Telefono etiqueta="Pastor" numero={estado.datos.telefono_pastor} />
              </div>

              <Redes
                titulo="Redes de la iglesia"
                redes={estado.datos.redes.filter((r) => r.tipo === 'propia')}
              />
              <Redes
                titulo="Redes relacionadas"
                redes={estado.datos.redes.filter((r) => r.tipo === 'relacionada')}
              />

              <h2 className="mt-6 text-xl font-semibold">
                {estado.datos.sedes.length === 1 ? 'Sede' : 'Sedes'}
              </h2>
              <ul className="mt-3 grid gap-3 md:grid-cols-2">
                {estado.datos.sedes.map((sede) => (
                  <li key={sede.id ?? sede.nombre} className="rounded-2xl bg-superficie-2 p-4">
                    <p className="font-semibold">{sede.nombre}</p>
                    <p className="mt-0.5 text-texto-suave">{sede.direccion}</p>
                    {esEnlaceSeguro(sede.enlace_maps) ? (
                      <a
                        href={sede.enlace_maps}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-2 inline-block font-semibold text-enlace underline-offset-4 hover:underline"
                      >
                        Abrir en Google Maps
                      </a>
                    ) : (
                      <p className="mt-2 text-sm text-texto-suave">Sin enlace de Google Maps.</p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          </article>
        )}
      </div>
    </section>
  )
}
