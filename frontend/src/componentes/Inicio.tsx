/** Pantalla por defecto de `/` mientras ningún módulo defina la suya. */
export default function Inicio() {
  return (
    <section>
      <h1 className="text-2xl font-bold text-primario">Bienvenido</h1>
      <p className="mt-2 text-slate-600">
        Presbiterio de la 3ra IAFCJ. Elige una opción del menú para comenzar.
      </p>
    </section>
  )
}
