import { StrictMode } from 'react'
import ReactDOM from 'react-dom/client'
import AppWidget from './AppWidget'
import './index.css'

// Widget entry point - renders the floating widget
ReactDOM.createRoot(document.getElementById('campusbot-widget')!).render(
  <StrictMode>
    <AppWidget />
  </StrictMode>,
)
