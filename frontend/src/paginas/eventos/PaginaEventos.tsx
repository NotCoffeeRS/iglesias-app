import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cancelarEvento, listarEventos, type Evento } from '../../api/eventos'
import { Cargando, ErrorConReintento } from './comunes'
import {
  claseBotonPrincipal,
  claseBotonSecundario,
  fechaLarga,
  hoyEnMerida,
  horaCorta,
  mensajeDeError,
  useCarga,
} from './utilidades'

function TarjetaEvento({ evento, alCambiar }: { evento: Evento; alCambiar: (e: Evento) => void }) {
  const [confirmando, setConfirmando] = useState(false)
  const [cancelando, setCancelando] = useState(false)
  const [error, setError] = useState('')

  async function cancelar() {
    setCancelando(true)
    setError('')
    try {
      alCambiar(await cancelarEvento(evento.id))
    } catch (e) {
      setError(mensajeDeError(e, 'cancelar el evento'))
      setCancelando(false)
    }
  }

  return (
    <li className="rounded-2xl border border-borde bg-superficie p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <h2 className={'text-lg font-semibold ' + (evento.cancelado ? 'line-through' : '')}>
            {evento.titulo}
          </h2>
          <p className="text-sm text-texto-suave">
            {fechaLarga(evento.fecha)} · {horaCorta(evento.hora)}
          </p>
        </div>
        {evento.cancelado && (
          <span className="rounded-full bg-peligro-fondo px-3 py-1 text-sm font-semibold text-peligro">
            Cancelado
          </span>
        )}
      </div>

      <p className="mt-2 text-sm">
        <span className="font-semibold">
          {evento.iglesia_id === null
            ? 'Todo el Presbiterio'
            : (evento.iglesia_nombre ?? 'Iglesia')}
        </span>
        {evento.lugar && <span className="text-texto-suave"> · {evento.lugar}</span>}
      </p>
      {evento.descripcion && <p className="mt-2 whitespace-pre-line">{evento.descripcion}</p>}

      {!evento.cancelado && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Link to={`/eventos/${evento.id}/editar`} className={claseBotonSecundario}>
            Editar
          </Link>
          {confirmando ? (
            <>
              <button
                type="button"
                onClick={cancelar}
                disabled={cancelando}
                className={claseBotonPrincipal}
              >
                {cancelando ? 'Cancelando…' : 'Sí, cancelar el evento'}
              </button>
              <button
                type="button"
                onClick={() => setConfirmando(false)}
                className={claseBotonSecundario}
              >
                No
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => setConfirmando(true)}
              className={claseBotonSecundario}
            >
              Cancelar evento
            </button>
          )}
        </div>
      )}
      {error && (
        <p role="alert" className="mt-2 text-sm text-peligro">
          {error}
        </p>
      )}
    </li>
  )
}

function Lista({ eventos }: { eventos: Evento[] }) {
  const [cambios, setCambios] = useState<Record<number, Evento>>({})
  if (eventos.length === 0) {
    return (
      <p className="rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
        No hay eventos próximos. Toca <strong>Nuevo evento</strong> para crear el primero.
      </p>
    )
  }
  return (
    <ul className="space-y-3">
      {eventos.map((e) => (
        <TarjetaEvento
          key={e.id}
          evento={cambios[e.id] ?? e}
          alCambiar={(nuevo) => setCambios((c) => ({ ...c, [nuevo.id]: nuevo }))}
        />
      ))}
    </ul>
  )
}

export default function PaginaEventos() {
  const aviso = (useLocation().state as { aviso?: string } | null)?.aviso
  const hoy = hoyEnMerida()
  const { estado, reintentar } = useCarga(() => listarEventos(hoy), 'ver los eventos', hoy)

  return (
    <section>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-bold">Eventos</h1>
        <Link to="/eventos/nuevo" className={claseBotonPrincipal}>
          Nuevo evento
        </Link>
      </div>
      <p className="mt-1 text-texto-suave">Los eventos de hoy en adelante, en orden.</p>
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
        {estado.tipo === 'listo' && <Lista eventos={estado.datos} />}
      </div>
    </section>
  )
}
