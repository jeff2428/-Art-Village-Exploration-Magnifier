import { useRef, useState, useEffect, useCallback } from 'react'
import { identifyPlant } from '../services/api'
import { savePokedexEntry } from '../services/storage'
import { prepareCapture, stopMediaStream } from './cameraLifecycle'
import './CameraView.css'

interface CameraViewProps {
  onOpenGallery: () => void
}

export default function CameraView({ onOpenGallery }: CameraViewProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [organ, setOrgan] = useState('auto')

  useEffect(() => {
    async function setupCamera() {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment' }
        })
        streamRef.current = mediaStream
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream
        }
      } catch (err: unknown) {
        setErrorMsg('相機權限遭拒或無法存取相機')
        console.error('Camera error', err)
      }
    }
    setupCamera()
    
    return () => {
      stopMediaStream(streamRef.current)
      streamRef.current = null
    }
  }, [])

  const captureAndIdentify = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current) return
    setIsProcessing(true)
    setErrorMsg('')

    const video = videoRef.current
    const canvas = canvasRef.current
    const ctx = prepareCapture(video, canvas)
    if (!ctx) {
      setIsProcessing(false)
      setErrorMsg('無法初始化影像擷取工具')
      return
    }
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    
    canvas.toBlob(async (blob) => {
      if (!blob) {
        setIsProcessing(false)
        setErrorMsg('無法擷取影像')
        return
      }

      const reader = new FileReader()
      reader.readAsDataURL(blob)
      reader.onloadend = async () => {
        const base64data = reader.result as string
        
        try {
          const result = await identifyPlant(blob, organ)
          
          const topMatch = result?.results?.[0]
          const scientificName = topMatch?.species?.scientificNameWithoutAuthor || 'Unknown'
          const commonName = topMatch?.species?.commonNames?.[0] || scientificName

          await savePokedexEntry({
            id: Date.now().toString(),
            name: commonName,
            type: 'plant',
            metadata: result,
            timestamp: Date.now()
          }, base64data)

          // Show success and move to gallery maybe? Or just show a toast
          onOpenGallery()
        } catch (err: unknown) {
          setErrorMsg(err instanceof Error ? err.message : '辨識失敗，請重試')
        } finally {
          setIsProcessing(false)
        }
      }
    }, 'image/jpeg', 0.8)
  }, [organ, onOpenGallery])

  return (
    <div className="camera-container">
      <video ref={videoRef} autoPlay playsInline muted className="camera-video" />
      <canvas ref={canvasRef} style={{ display: 'none' }} />
      
      <div className="magnifier-overlay">
        <div className="magnifier-circle" />
      </div>

      <div className="controls-container">
        {errorMsg && <div className="error-toast">{errorMsg}</div>}
        
        <div className="organ-selector">
          <select value={organ} onChange={e => setOrgan(e.target.value)} disabled={isProcessing}>
            <option value="auto">自動 (Auto)</option>
            <option value="leaf">葉 (Leaf)</option>
            <option value="flower">花 (Flower)</option>
            <option value="fruit">果 (Fruit)</option>
            <option value="bark">樹皮 (Bark)</option>
          </select>
        </div>

        <div className="action-buttons">
          <button className="btn gallery-btn" onClick={onOpenGallery} disabled={isProcessing}>
            📖 圖鑑
          </button>
          <button className="capture-btn" onClick={captureAndIdentify} disabled={isProcessing}>
            <div className={`capture-btn-inner ${isProcessing ? 'pulsing' : ''}`} />
          </button>
          <div style={{width: '90px'}} /> {/* spacer */}
        </div>
      </div>
      
      {isProcessing && (
        <div className="loading-overlay glass-panel">
          <div className="spinner" />
          <p>辨識中...</p>
        </div>
      )}
    </div>
  )
}
