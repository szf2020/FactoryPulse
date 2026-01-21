import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

/**
 * Application Entry Point.
 * Mounts the main React application into the DOM root element.
 * Imports global styles, including Tailwind CSS directives.
 */
ReactDOM.createRoot(document.getElementById('root')).render(
  // StrictMode enables additional checks and warnings during development
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)