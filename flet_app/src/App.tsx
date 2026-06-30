import { lazy, Suspense, useState, useEffect } from 'react'
import './App.css'
import CameraView from './components/CameraView'
import ErrorBoundary from './components/ErrorBoundary'
import { initDB } from './services/storage'

const Gallery = lazy(() => import('./components/Gallery'))
const Admin = lazy(() => import('./components/Admin'))

function App() {
  const [view, setView] = useState<'camera' | 'gallery'>('camera')
  const [isDbReady, setIsDbReady] = useState(false)

  useEffect(() => {
    initDB().then(() => setIsDbReady(true)).catch(console.error)
  }, [])

  if (!isDbReady) return <div className="loading-screen">載入探險工具中...</div>

  if (window.location.pathname === '/admin') {
    return (
      <ErrorBoundary>
        <Suspense fallback={<div className="loading-screen">載入管理頁面...</div>}>
          <Admin />
        </Suspense>
      </ErrorBoundary>
    )
  }

  return (
    <ErrorBoundary>
      <div className="app-container">
        {view === 'camera' ? (
          <CameraView onOpenGallery={() => setView('gallery')} />
        ) : (
          <Suspense fallback={<div className="loading-screen">載入圖鑑...</div>}>
            <Gallery onClose={() => setView('camera')} />
          </Suspense>
        )}
      </div>
    </ErrorBoundary>
  )
}

export default App
