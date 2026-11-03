import '@fontsource-variable/atkinson-hyperlegible-next/wght.css'
import '@fontsource-variable/bricolage-grotesque/standard.css'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
