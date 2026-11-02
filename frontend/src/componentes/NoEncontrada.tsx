import { Link } from 'react-router-dom'

export default function NoEncontrada() {
  return (
    <section className="py-10 text-center">
      <h1 className="text-2xl font-bold text-primario">Página no encontrada</h1>
      <p className="mt-2 text-slate-600">La dirección que buscas no existe.</p>
      <Link
        to="/"
        className="mt-6 inline-block rounded-lg bg-primario px-5 py-2.5 font-medium text-white hover:bg-primario-claro"
      >
        Volver al inicio
      </Link>
    </section>
  )
}
