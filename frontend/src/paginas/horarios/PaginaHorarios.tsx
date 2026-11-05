import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  actualizarHorario,
  crearHorario,
  DIAS,
  eliminarHorario,
  listarHorarios,
  listarSedes,
  type HorarioEntrada,
  type SedeResumen,
} from '../../api/horarios'
import FormularioHorario from './FormularioHorario'
import {
  claseBotonPrincipal,
  claseCampo,
  mensajeDeError,
  nombreTipo,
  rangoHora,
  useCarga,
} from './utilidades'

function Cargando() {
  return (
    <div className="space-y-3" aria-hidden="true">
      {[0, 1, 2].map((i) => (
        <div key={i} className="h-16 animate-pulse rounded-2xl bg-superficie" />
      ))}
    </div>
  )
}

function ErrorConReintento({ mensaje, reintentar }: { mensaje: string; reintentar: () => void }) {
  return (
    <div role="alert" className="rounded-3xl border border-borde bg-superficie p-6 text-center">
      <p className="font-semibold">{mensaje}</p>
      <button type="button" onClick={reintentar} className={claseBotonPrincipal + ' mt-4'}>
        Reintentar
      </button>
    </div>
  )
}

const claseBotonFila =
  'rounded-lg px-2.5 py-1.5 text-sm font-semibold transition-colors hover:bg-resalte'

function HorariosDeSede({ sede }: { sede: SedeResumen }) {
  const { estado, recargar } = useCarga(
    () => listarHorarios(sede.id),
    'cargar los horarios',
    sede.id,
  )
  // null = nada abierto; 'nuevo' = agregando; número = editando ese horario
  const [editando, setEditando] = useState<'nuevo' | number | null>(null)
  const [confirmandoQuitar, setConfirmandoQuitar] = useState<number | null>(null)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [aviso, setAviso] = useState<string | null>(null)

  function abrir(cual: 'nuevo' | number) {
    setEditando(cual)
    setConfirmandoQuitar(null)
    setError(null)
    setAviso(null)
  }

  async function guardar(datos: HorarioEntrada) {
    setGuardando(true)
    setError(null)
    try {
      if (editando === 'nuevo') await crearHorario(sede.id, datos)
      else if (typeof editando === 'number') await actualizarHorario(editando, datos)
      setAviso(editando === 'nuevo' ? 'Horario agregado.' : 'Horario actualizado.')
      setEditando(null)
      recargar(true)
    } catch (e) {
      setError(mensajeDeError(e, 'editar los horarios de esta sede'))
    } finally {
      setGuardando(false)
    }
  }

  async function quitar(id: number) {
    setGuardando(true)
    setAviso(null)
    try {
      await eliminarHorario(id)
      setAviso('Horario quitado.')
      setConfirmandoQuitar(null)
      recargar(true)
    } catch (e) {
      setAviso(null)
      setError(mensajeDeError(e, 'quitar este horario'))
    } finally {
      setGuardando(false)
    }
  }

  if (estado.tipo === 'cargando') return <Cargando />
  if (estado.tipo === 'error')
    return <ErrorConReintento mensaje={estado.mensaje} reintentar={() => recargar()} />

  const porDia = DIAS.map((dia) => ({
    ...dia,
    horarios: estado.datos
      .filter((h) => h.dia === dia.clave)
      .sort((a, b) => a.hora_inicio.localeCompare(b.hora_inicio)),
  })).filter((d) => d.horarios.length > 0)

  return (
    <div className="space-y-4">
      {aviso && (
        <p
          role="status"
          className="rounded-xl bg-acento px-4 py-2.5 font-semibold text-acento-texto"
        >
          {aviso}
        </p>
      )}
      {error && editando === null && (
        <p role="alert" className="rounded-xl bg-peligro-fondo px-4 py-2.5 text-peligro">
          {error}
        </p>
      )}

      {editando === 'nuevo' ? (
        <FormularioHorario
          guardando={guardando}
          error={error}
          onGuardar={guardar}
          onCancelar={() => setEditando(null)}
        />
      ) : (
        <button type="button" onClick={() => abrir('nuevo')} className={claseBotonPrincipal}>
          Agregar horario
        </button>
      )}

      {porDia.length === 0 && editando !== 'nuevo' && (
        <p className="rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
          {sede.nombre} todavía no tiene horarios. Agrega el primero para que aparezca en la página
          pública.
        </p>
      )}

      {porDia.map((dia) => (
        <section key={dia.clave} className="rounded-3xl border border-borde bg-superficie p-4">
          <h2 className="px-1 text-lg font-semibold">{dia.nombre}</h2>
          <ul className="mt-2 divide-y divide-borde">
            {dia.horarios.map((h) =>
              editando === h.id ? (
                <li key={h.id} className="py-3">
                  <FormularioHorario
                    inicial={h}
                    guardando={guardando}
                    error={error}
                    onGuardar={guardar}
                    onCancelar={() => setEditando(null)}
                  />
                </li>
              ) : (
                <li key={h.id} className="flex flex-wrap items-center gap-x-3 gap-y-1 px-1 py-3">
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold">{nombreTipo(h.tipo)}</p>
                    <p className="text-sm text-texto-suave tabular-nums">
                      {rangoHora(h)}
                      {h.descripcion && <span className="block">{h.descripcion}</span>}
                    </p>
                  </div>
                  {confirmandoQuitar === h.id ? (
                    <div className="flex items-center gap-1">
                      <span className="text-sm text-texto-suave">¿Quitar?</span>
                      <button
                        type="button"
                        disabled={guardando}
                        onClick={() => quitar(h.id)}
                        className={claseBotonFila + ' text-peligro hover:bg-peligro-fondo'}
                      >
                        Sí, quitar
                      </button>
                      <button
                        type="button"
                        onClick={() => setConfirmandoQuitar(null)}
                        className={claseBotonFila}
                      >
                        No
                      </button>
                    </div>
                  ) : (
                    <div className="flex gap-1">
                      <button
                        type="button"
                        onClick={() => abrir(h.id)}
                        className={claseBotonFila + ' text-enlace'}
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setConfirmandoQuitar(h.id)
                          setAviso(null)
                          setError(null)
                        }}
                        className={claseBotonFila + ' text-peligro hover:bg-peligro-fondo'}
                      >
                        Quitar
                      </button>
                    </div>
                  )}
                </li>
              ),
            )}
          </ul>
        </section>
      ))}
    </div>
  )
}

export default function PaginaHorarios() {
  const { estado, recargar } = useCarga(listarSedes, 'cargar las sedes')
  const [parametros, setParametros] = useSearchParams()

  const sedes = estado.tipo === 'listo' ? estado.datos : []
  const elegida = sedes.find((s) => String(s.id) === parametros.get('sede')) ?? sedes[0]

  return (
    <section>
      <h1 className="text-3xl font-bold md:text-4xl">Horarios</h1>
      <p className="mt-1 text-texto-suave">
        Agrega, cambia o quita los horarios de cada sede. Se publican en la página de horarios y
        ubicaciones.
      </p>

      <div className="mt-6 space-y-5">
        {estado.tipo === 'cargando' && <Cargando />}
        {estado.tipo === 'error' && (
          <ErrorConReintento mensaje={estado.mensaje} reintentar={() => recargar()} />
        )}
        {estado.tipo === 'listo' && sedes.length === 0 && (
          <p className="rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
            No tienes sedes a tu cargo. Pide al pastor o al presbítero que te dé acceso.
          </p>
        )}

        {elegida && (
          <>
            {sedes.length > 1 && (
              <label className="block max-w-md text-sm font-semibold">
                Sede
                <select
                  value={elegida.id}
                  onChange={(e) => setParametros({ sede: e.target.value }, { replace: true })}
                  className={claseCampo}
                >
                  {sedes.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.iglesia_nombre} — {s.nombre}
                    </option>
                  ))}
                </select>
              </label>
            )}
            {sedes.length === 1 && (
              <p className="font-semibold">
                {elegida.iglesia_nombre} — {elegida.nombre}
              </p>
            )}
            <HorariosDeSede key={elegida.id} sede={elegida} />
          </>
        )}
      </div>
    </section>
  )
}
