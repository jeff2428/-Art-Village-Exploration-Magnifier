import { useState } from 'react'
import {
  BookOpen,
  Camera,
} from '@phosphor-icons/react'
import { useCamera } from '../hooks/useCamera'
import { usePlantIdentification } from '../hooks/usePlantIdentification'
import OrganSelector from './OrganSelector'
import './CameraView.css'

interface CameraViewProps {
  onOpenGallery: () => void
}

export default function CameraView({ onOpenGallery }: CameraViewProps) {
  const { videoRef, canvasRef, isReady, errorMsg: cameraError, prepareCapture } = useCamera()
  const { identify, isProcessing, errorMsg: identifyError } = usePlantIdentification(onOpenGallery)
  const [organ, setOrgan] = useState('auto')

  const errorMsg = cameraError || identifyError

  const handleCapture = () => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return

    const ctx = prepareCapture()
    if (!ctx) return

    identify(video, canvas, organ)
  }

  return (
    <div className="camera-container">
      <canvas ref={canvasRef} className="capture-canvas" />

      <main className="camera-workbench">
        <section className="magnifier-stage" aria-label="植物探索相機">
          <div className="magnifier-tool">
            <img
              src="/assets/ui/wooden-magnifier-tool.png"
              alt=""
              className="magnifier-tool-image"
              aria-hidden="true"
            />

            <div className="lens-window">
              <video ref={videoRef} autoPlay playsInline muted className="camera-video" />
            </div>

            <button
              type="button"
              className="tool-control gallery-tool-button"
              onClick={onOpenGallery}
              disabled={isProcessing}
              aria-label="開啟圖鑑"
            >
              <BookOpen size={30} weight="fill" aria-hidden="true" />
              <span>圖鑑</span>
            </button>

            <button
              type="button"
              className={`tool-control capture-tool-button ${isProcessing ? 'is-processing' : ''}`}
              onClick={handleCapture}
              disabled={isProcessing || !isReady}
              aria-label="拍照辨識"
            >
              <Camera size={34} weight="fill" aria-hidden="true" />
              <span>{isProcessing ? '辨識中' : '拍照'}</span>
            </button>
          </div>
        </section>

        <OrganSelector organ={organ} onSelect={setOrgan} disabled={isProcessing} />

        <div className="camera-status" role="status" aria-live="polite">
          <span className={`status-dot ${errorMsg ? 'has-error' : ''}`} aria-hidden="true" />
          <p>
            {errorMsg || (isProcessing
              ? '正在比對植物特徵，請保持畫面穩定'
              : '相機準備完成，將植物置於圓形鏡面中央')}
          </p>
        </div>
      </main>
    </div>
  )
}
