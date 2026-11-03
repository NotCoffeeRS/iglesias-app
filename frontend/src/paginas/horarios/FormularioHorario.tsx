import { useState, type FormEvent } from 'react'
import { DIAS, TIPOS, type Horario, type HorarioEntrada } from '../../api/horarios'
import { claseBotonPrincipal, claseBotonSecundario, claseCampo } from './utilidades'

interface Props {
  /** Si se pasa, se edita ese horario; si no, se agrega uno nuevo. */
  inicial?: Horario
  guardando: boolean
  error: string | null
  onGuardar: (datos: HorarioEntrada) => void
  onCancelar: () => void
}

const recortarHora = (hora?: string | null) => (hora ? hora.slice(0, 5) : '')

export default function FormularioHorario({
  inicial,
  guardando,
  error,
  onGuardar,
  onCancelar,
}: Props) {
  const [tipo, setTipo] = useState(inicial?.tipo ?? 'culto_domingo')
  const [dia, setDia] = useState(inicial?.dia ?? 'domingo')
  const [inicio, setInicio] = useState(recortarHora(inicial?.hora_inicio))
  const [fin, setFin] = useState(recortarHora(inicial?.hora_fin))
  const [descripcion, setDescripcion] = useState(inicial?.descripcion ?? '')
  const [errores, setErrores] = useState<{ inicio?: string; fin?: string }>({})

  function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const encontrados: typeof errores = {}
    if (!inicio) encontrados.inicio = 'Indica a qué hora empieza.'
    if (inicio && fin && fin <= inicio) encontrados.fin = 'Debe ser después de la hora de inicio.'
    setErrores(encontrados)
    if (Object.keys(encontrados).length > 0) return
    onGuardar({
      tipo,
      dia,
      hora_inicio: inicio,
      hora_fin: fin || null,
      descripcion: descripcion.trim() || null,
    })
  }

  return (
    <form
      onSubmit={enviar}
      noValidate
      className="space-y-4 rounded-3xl border-2 border-acento bg-superficie p-5"
    >
      <h2 className="text-lg font-semibold">{inicial ? 'Editar horario' : 'Nuevo horario'}</h2>

      {error && (
        <p role="alert" className="rounded-xl bg-peligro-fondo px-4 py-2.5 text-peligro">
          {error}
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm font-semibold">
          Tipo de servicio
          <select
            value={tipo}
            onChange={(e) => setTipo(e.target.value as Horario['tipo'])}
            className={claseCampo}
          >
            {TIPOS.map((t) => (
              <option key={t.clave} value={t.clave}>
                {t.nombre}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm font-semibold">
          Día
          <select
            value={dia}
            onChange={(e) => setDia(e.target.value as Horario['dia'])}
            className={claseCampo}
          >
            {DIAS.map((d) => (
              <option key={d.clave} value={d.clave}>
                {d.nombre}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm font-semibold">
          Empieza
          <input
            type="time"
            value={inicio}
            onChange={(e) => setInicio(e.target.value)}
            aria-invalid={errores.inicio ? true : undefined}
            className={claseCampo}
          />
          {errores.inicio && (
            <span className="mt-1 block font-normal text-peligro">{errores.inicio}</span>
          )}
        </label>
        <label className="block text-sm font-semibold">
          Termina
          <input
            type="time"
            value={fin}
            onChange={(e) => setFin(e.target.value)}
            aria-invalid={errores.fin ? true : undefined}
            className={claseCampo}
          />
          {errores.fin ? (
            <span className="mt-1 block font-normal text-peligro">{errores.fin}</span>
          ) : (
            <span className="mt-1 block font-normal text-texto-suave">Opcional.</span>
          )}
        </label>
      </div>

      <label className="block text-sm font-semibold">
        Nota
        <input
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          placeholder="Ej. Reunión de jóvenes en el salón"
          className={claseCampo}
        />
        <span className="mt-1 block font-normal text-texto-suave">
          Opcional. Se ve en la página pública.
        </span>
      </label>

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={guardando}
          className={claseBotonPrincipal + ' flex-1 sm:flex-none'}
        >
          {guardando ? 'Guardando…' : inicial ? 'Guardar cambios' : 'Agregar horario'}
        </button>
        <button type="button" onClick={onCancelar} className={claseBotonSecundario}>
          Cancelar
        </button>
      </div>
    </form>
  )
}
