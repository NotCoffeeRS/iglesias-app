import { useState, type FormEvent } from 'react'
import {
  listarIglesias,
  obtenerReporte,
  SERVICIOS,
  type Filtro,
} from '../../api/reporte_asistencia'
import { obtenerYo } from '../../api/usuarios'
import {
  claseBotonPrincipal,
  claseBotonSecundario,
  claseCampo,
  hoyEnMerida,
} from '../miembros/utilidades'
import { useCarga } from './utilidades'

function Panel({
  iglesias,
  limitado,
}: {
  iglesias: { id: number; nombre: string }[]
  limitado: boolean
}) {
  const hoy = hoyEnMerida()
  const [desde, setDesde] = useState(hoy.slice(0, 8) + '01')
  const [hasta, setHasta] = useState(hoy)
  const [iglesia, setIglesia] = useState('')
  const [servicio, setServicio] = useState('')
  const [error, setError] = useState('')
  const [consulta, setConsulta] = useState<Filtro>({ desde, hasta })
  const { estado, reintentar } = useCarga(() => obtenerReporte(consulta), JSON.stringify(consulta))
  function aplicar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!desde || !hasta || desde > hasta) {
      setError('Indica un periodo válido: desde debe ser anterior o igual a hasta.')
      return
    }
    setError('')
    setConsulta({
      desde,
      hasta,
      iglesia_id: iglesia ? Number(iglesia) : undefined,
      servicio: servicio || undefined,
    })
    reintentar()
  }
  return (
    <div className="space-y-5">
      {limitado && (
        <p className="rounded-xl border border-borde p-4">
          El alcance usa los grupos y asignaciones actuales: los grupos que diriges o, para ujieres,
          miembros sin célula.
        </p>
      )}
      <form
        onSubmit={aplicar}
        className="grid gap-4 rounded-2xl border border-borde bg-superficie p-5 sm:grid-cols-2"
      >
        <label className="text-sm font-semibold">
          Desde
          <input
            className={claseCampo}
            type="date"
            value={desde}
            onChange={(e) => setDesde(e.target.value)}
            required
          />
        </label>
        <label className="text-sm font-semibold">
          Hasta
          <input
            className={claseCampo}
            type="date"
            value={hasta}
            onChange={(e) => setHasta(e.target.value)}
            required
          />
        </label>
        <label className="text-sm font-semibold">
          Iglesia
          <select
            className={claseCampo}
            value={iglesia}
            onChange={(e) => setIglesia(e.target.value)}
          >
            <option value="">Todas en mi alcance</option>
            {iglesias.map((i) => (
              <option key={i.id} value={i.id}>
                {i.nombre}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm font-semibold">
          Servicio
          <select
            className={claseCampo}
            value={servicio}
            onChange={(e) => setServicio(e.target.value)}
          >
            <option value="">Todos los servicios</option>
            {SERVICIOS.map(([clave, nombre]) => (
              <option key={clave} value={clave}>
                {nombre}
              </option>
            ))}
          </select>
        </label>
        {error && (
          <p role="alert" className="text-peligro sm:col-span-2">
            {error}
          </p>
        )}
        <button className={claseBotonPrincipal} type="submit">
          Consultar reporte
        </button>
      </form>
      {estado.tipo === 'cargando' && <p role="status">Cargando reporte…</p>}
      {estado.tipo === 'error' && (
        <div role="alert">
          <p>{estado.mensaje}</p>
          <button className={claseBotonSecundario} onClick={reintentar}>
            Reintentar
          </button>
        </div>
      )}
      {estado.tipo === 'listo' && (
        <>
          <p className="text-sm text-texto-suave">
            Periodo consultado: {estado.datos.desde} a {estado.datos.hasta}.
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            {(
              [
                ['Registros', estado.datos.totales.registros],
                ['Asistencias', estado.datos.totales.asistencias],
                ['Faltas', estado.datos.totales.faltas],
              ] as const
            ).map(([nombre, valor]) => (
              <div key={nombre} className="rounded-2xl border border-borde bg-superficie p-5">
                <p className="text-texto-suave">{nombre}</p>
                <p className="text-3xl font-bold">{valor}</p>
              </div>
            ))}
          </div>
          {estado.datos.totales.registros === 0 && (
            <p role="status" className="rounded-xl border border-borde p-4">
              No hay marcas guardadas en este periodo y alcance. No se consideran faltas los días
              sin captura.
            </p>
          )}
          {estado.datos.iglesias.map((i) => (
            <section
              key={i.iglesia_id}
              className="space-y-3 rounded-2xl border border-borde bg-superficie p-5"
            >
              <h2 className="text-xl font-semibold">{i.iglesia_nombre}</h2>
              <p>
                {i.asistencias} asistencias · {i.faltas} faltas · {i.registros} registros
              </p>
              {i.detalle.length > 0 ? (
                <div
                  className="overflow-x-auto"
                  role="region"
                  aria-label={`Detalle de ${i.iglesia_nombre}`}
                  tabIndex={0}
                >
                  <table className="w-full text-left text-sm">
                    <caption className="sr-only">Marcas por fecha y servicio</caption>
                    <thead>
                      <tr>
                        {['Fecha', 'Servicio', 'Asistencias', 'Faltas', 'Registros'].map((t) => (
                          <th key={t} scope="col" className="px-3 py-2">
                            {t}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {i.detalle.map((d) => (
                        <tr key={d.fecha + d.servicio} className="border-t border-borde">
                          <td className="px-3 py-2 whitespace-nowrap">{d.fecha}</td>
                          <td className="px-3 py-2">
                            {SERVICIOS.find(([c]) => c === d.servicio)?.[1] ?? d.servicio}
                          </td>
                          <td className="px-3 py-2">{d.asistencias}</td>
                          <td className="px-3 py-2">{d.faltas}</td>
                          <td className="px-3 py-2">{d.registros}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-texto-suave">Sin registros dentro de tu alcance.</p>
              )}
            </section>
          ))}
        </>
      )}
    </div>
  )
}

export default function PaginaReporte() {
  const { estado, reintentar } = useCarga(async () => {
    const yo = await obtenerYo()
    if (yo.cargo === 'tesorero') return null
    return {
      iglesias: await listarIglesias(),
      limitado: !['presbitero', 'pastor', 'apoyo_pastor'].includes(yo.cargo),
    }
  })
  if (estado.tipo === 'cargando') return <p role="status">Cargando…</p>
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
    return <p role="alert">Tu cargo no tiene acceso al reporte de asistencia.</p>
  return (
    <section className="space-y-5">
      <h1 className="text-3xl font-bold">Reporte de asistencia</h1>
      <p className="text-texto-suave">
        Totales de marcas guardadas por iglesia, fecha y servicio. Una persona puede tener registros
        en varias fechas; no es un conteo de personas distintas.
      </p>
      <Panel {...estado.datos} />
    </section>
  )
}
