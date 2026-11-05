import { useState, type FormEvent } from 'react'
import {
  asignarMiembro,
  listarCandidatos,
  listarGrupos,
  listarIntegrantes,
  quitarMiembro,
  type GrupoAsignaciones,
} from '../../api/asignaciones'
import { TIPOS_GRUPO } from '../../api/grupos'
import { ESTADOS } from '../../api/miembros'
import { obtenerYo } from '../../api/usuarios'
import { claseBotonPrincipal, claseBotonSecundario, claseCampo } from '../miembros/utilidades'
import { mensaje, useCarga } from './utilidades'

function Integrantes({ grupo, gestor }: { grupo: GrupoAsignaciones; gestor: boolean }) {
  const [seleccionado, setSeleccionado] = useState('')
  const [porQuitar, setPorQuitar] = useState<number | null>(null)
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState('')
  const [aviso, setAviso] = useState('')
  const { estado, reintentar } = useCarga(async () => {
    const [miembros, candidatos] = await Promise.all([
      listarIntegrantes(grupo.id),
      gestor && grupo.activo ? listarCandidatos(grupo.id) : Promise.resolve([]),
    ])
    return { miembros, candidatos }
  }, grupo.id)

  async function operar(accion: () => Promise<unknown>, texto: string) {
    if (ocupado) return
    setOcupado(true)
    setError('')
    setAviso('')
    try {
      await accion()
      setAviso(texto)
      setSeleccionado('')
      setPorQuitar(null)
      reintentar()
    } catch (e) {
      setError(mensaje(e))
    } finally {
      setOcupado(false)
    }
  }
  function agregar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    if (!seleccionado) {
      setError('Elige el miembro que quieres agregar.')
      return
    }
    void operar(() => asignarMiembro(grupo.id, Number(seleccionado)), 'Integrante agregado.')
  }

  if (estado.tipo === 'cargando') return <p role="status">Cargando integrantes…</p>
  if (estado.tipo === 'error')
    return (
      <div role="alert">
        <p>{estado.mensaje}</p>
        <button className={claseBotonSecundario} onClick={reintentar}>
          Reintentar
        </button>
      </div>
    )
  return (
    <section className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold">{grupo.nombre}</h2>
        <p className="text-sm text-texto-suave">
          {grupo.iglesia_nombre} ·{' '}
          {TIPOS_GRUPO.find((t) => t.clave === grupo.tipo)?.nombre ?? 'Grupo'}
        </p>
      </div>
      {!grupo.activo && (
        <p className="rounded-xl border border-borde p-4">
          Este grupo está inactivo. Puedes quitar integrantes, pero no agregar nuevos.
        </p>
      )}
      {!gestor && (
        <p className="rounded-xl border border-borde bg-superficie p-4">
          Puedes quitar integrantes de los grupos que diriges. El pastor o su apoyo agregan nuevos
          miembros.
        </p>
      )}
      {aviso && (
        <p role="status" className="rounded-xl bg-acento p-3 text-acento-texto">
          {aviso}
        </p>
      )}
      {error && (
        <p role="alert" className="rounded-xl bg-peligro-fondo p-4 text-peligro">
          {error}
        </p>
      )}
      {gestor && grupo.activo && (
        <form
          onSubmit={agregar}
          className="space-y-3 rounded-2xl border border-borde bg-superficie p-5"
        >
          <label className="block text-sm font-semibold">
            Miembro para agregar
            <select
              className={claseCampo}
              value={seleccionado}
              onChange={(e) => setSeleccionado(e.target.value)}
              disabled={ocupado || estado.datos.candidatos.length === 0}
            >
              <option value="">Elige un miembro</option>
              {estado.datos.candidatos.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.nombre} · {ESTADOS.find((e) => e.clave === m.estado)?.nombre ?? m.estado}
                </option>
              ))}
            </select>
          </label>
          {estado.datos.candidatos.length === 0 && (
            <p className="text-sm text-texto-suave">
              No hay miembros disponibles para agregar a este grupo.
            </p>
          )}
          {grupo.tipo === 'celula' && (
            <p className="text-sm text-texto-suave">
              Cada miembro puede pertenecer a una sola célula. Para cambiarlo, quita primero su
              asignación anterior.
            </p>
          )}
          <button className={claseBotonPrincipal} type="submit" disabled={ocupado || !seleccionado}>
            {ocupado ? 'Guardando…' : 'Agregar al grupo'}
          </button>
        </form>
      )}
      <h3 className="font-semibold">Integrantes ({estado.datos.miembros.length})</h3>
      {estado.datos.miembros.length === 0 ? (
        <p className="rounded-2xl border border-borde bg-superficie p-5">
          Este grupo todavía no tiene integrantes asignados.
        </p>
      ) : (
        <ul className="space-y-3">
          {estado.datos.miembros.map((m) => (
            <li key={m.id} className="rounded-2xl border border-borde bg-superficie p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-semibold break-words">{m.nombre}</p>
                  <p className="text-sm text-texto-suave">
                    {ESTADOS.find((e) => e.clave === m.estado)?.nombre ?? m.estado}
                  </p>
                </div>
                <button
                  className={claseBotonSecundario + ' text-peligro!'}
                  type="button"
                  onClick={() => setPorQuitar(m.id)}
                  disabled={ocupado}
                  aria-label={`Quitar del grupo a ${m.nombre}`}
                >
                  Quitar
                </button>
              </div>
              {porQuitar === m.id && (
                <div className="mt-4 space-y-3 rounded-xl border border-borde p-4">
                  <p>¿Quitar a {m.nombre} de este grupo? Su ficha de miembro se conserva.</p>
                  <div className="flex flex-wrap gap-3">
                    <button
                      type="button"
                      className={
                        claseBotonPrincipal + ' bg-peligro! hover:bg-peligro! hover:opacity-90'
                      }
                      disabled={ocupado}
                      onClick={() =>
                        void operar(
                          () => quitarMiembro(grupo.id, m.id),
                          'Asignación retirada. La ficha de miembro se conserva.',
                        )
                      }
                    >
                      Sí, quitar
                    </button>
                    <button
                      type="button"
                      className={claseBotonSecundario}
                      disabled={ocupado}
                      onClick={() => setPorQuitar(null)}
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function Selector({ grupos, gestor }: { grupos: GrupoAsignaciones[]; gestor: boolean }) {
  const [elegido, setElegido] = useState(grupos.length === 1 ? String(grupos[0].id) : '')
  const grupo = grupos.find((g) => String(g.id) === elegido)
  return (
    <div className="space-y-6">
      <label className="block text-sm font-semibold">
        Grupo
        <select className={claseCampo} value={elegido} onChange={(e) => setElegido(e.target.value)}>
          <option value="">Elige un grupo</option>
          {grupos.map((g) => (
            <option key={g.id} value={g.id}>
              {g.nombre} · {g.iglesia_nombre}
              {g.activo ? '' : ' (inactivo)'}
            </option>
          ))}
        </select>
      </label>
      {grupo ? (
        <Integrantes key={grupo.id} grupo={grupo} gestor={gestor} />
      ) : (
        <p className="text-texto-suave">Elige el grupo cuyos integrantes quieres consultar.</p>
      )}
    </div>
  )
}

export default function PaginaAsignaciones() {
  const { estado, reintentar } = useCarga(async () => {
    const yo = await obtenerYo()
    if (yo.cargo === 'tesorero') return null
    return {
      grupos: await listarGrupos(),
      gestor: ['presbitero', 'pastor', 'apoyo_pastor'].includes(yo.cargo),
    }
  })
  if (estado.tipo === 'cargando') return <p role="status">Cargando grupos…</p>
  if (estado.tipo === 'error')
    return (
      <div role="alert">
        <p>{estado.mensaje}</p>
        <button className={claseBotonSecundario} onClick={reintentar}>
          Reintentar
        </button>
      </div>
    )
  if (estado.datos === null)
    return <p role="alert">No tienes acceso a las asignaciones de grupos.</p>
  return (
    <section className="mx-auto max-w-3xl space-y-5">
      <h1 className="text-3xl font-bold">Asignaciones a grupos</h1>
      <p className="text-texto-suave">
        Consulta y organiza los integrantes de cada grupo y célula.
      </p>
      {estado.datos.grupos.length === 0 ? (
        <p className="rounded-2xl border border-borde bg-superficie p-5">
          No tienes grupos en tu alcance. Si eres líder, pide al pastor que vincule tu cuenta con tu
          ficha de miembro y te registre como líder del grupo.
        </p>
      ) : (
        <Selector {...estado.datos} />
      )}
    </section>
  )
}
