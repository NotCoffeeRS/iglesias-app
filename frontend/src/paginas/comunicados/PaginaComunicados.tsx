import { Link, useLocation } from 'react-router-dom'
import { listarComunicados, type Comunicado } from '../../api/comunicados'
import { Cargando, ErrorConReintento } from './comunes'
import {
  claseBotonPrincipal,
  claseBotonSecundario,
  fechaLarga,
  fechaPublicacion,
  useCarga,
} from './utilidades'

function TarjetaComunicado({ comunicado }: { comunicado: Comunicado }) {
  return (
    <li className="rounded-2xl border border-borde bg-superficie p-4">
      <h2 className="break-words text-lg font-semibold">{comunicado.titulo}</h2>
      <p className="text-sm text-texto-suave">
        <span className="font-semibold text-texto">
          {comunicado.iglesia_id === null
            ? 'Todo el Presbiterio'
            : (comunicado.iglesia_nombre ?? 'Iglesia')}
        </span>{' '}
        · publicado el {fechaPublicacion(comunicado.publicado_en)} · vigente hasta{' '}
        {fechaLarga(comunicado.vigente_hasta)}
      </p>
      <p className="mt-2 whitespace-pre-line break-words">{comunicado.contenido}</p>
      <div className="mt-3">
        <Link
          to={`/comunicados/${comunicado.id}/editar`}
          aria-label={`Editar ${comunicado.titulo}`}
          className={claseBotonSecundario}
        >
          Editar
        </Link>
      </div>
    </li>
  )
}

function Lista({ comunicados }: { comunicados: Comunicado[] }) {
  if (comunicados.length === 0) {
    return (
      <p className="rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
        No hay comunicados vigentes. Toca <strong>Nuevo comunicado</strong> para publicar el
        primero.
      </p>
    )
  }
  return (
    <ul className="space-y-3">
      {comunicados.map((c) => (
        <TarjetaComunicado key={c.id} comunicado={c} />
      ))}
    </ul>
  )
}

export default function PaginaComunicados() {
  const aviso = (useLocation().state as { aviso?: string } | null)?.aviso
  const { estado, reintentar } = useCarga(listarComunicados, 'ver los comunicados', 'vigentes')

  return (
    <section>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-bold">Comunicados</h1>
        <Link to="/comunicados/nuevo" className={claseBotonPrincipal}>
          Nuevo comunicado
        </Link>
      </div>
      <p className="mt-1 text-texto-suave">Solo se muestran los comunicados vigentes.</p>
      {aviso && (
        <p role="status" className="mt-3 rounded-xl bg-superficie px-4 py-2.5 font-semibold">
          {aviso}
        </p>
      )}
      <div className="mt-4">
        {estado.tipo === 'cargando' && <Cargando />}
        {estado.tipo === 'error' && (
          <ErrorConReintento mensaje={estado.mensaje} reintentar={reintentar} />
        )}
        {estado.tipo === 'listo' && <Lista comunicados={estado.datos} />}
      </div>
    </section>
  )
}
