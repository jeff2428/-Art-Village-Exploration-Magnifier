import { useState, useEffect } from 'react'
import './App.css'
import CameraView from './components/CameraView'
import Gallery from './components/Gallery'
import Admin from './components/Admin'
import { initDB } from './services/storage'

function App() {
  const [view, setView] = useState<'camera' | 'gallery'>('camera')
  const [isDbReady, setIsDbReady] = useState(false)

  useEffect(() => {
    initDB().then(() => setIsDbReady(true)).catch(console.error)
  }, [])

  if (!isDbReady) return <div className="loading-screen">載入探險工具中...</div>

  if (window.location.pathname === '/admin') {
    return <Admin />
  }

  return (
    <div className="app-container">
      {view === 'camera' ? (
        <CameraView onOpenGallery={() => setView('gallery')} />
      ) : (
        <Gallery onClose={() => setView('camera')} />
      )}
    </div>
  )
}

export default App
