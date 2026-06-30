import { useCallback, useState } from 'react'
import { identifyPlant } from '../services/api'
import { savePokedexEntry } from '../services/storage'

export interface UsePlantIdentificationReturn {
  identify: (video: HTMLVideoElement, canvas: HTMLCanvasElement, organ: string) => Promise<void>
  isProcessing: boolean
  errorMsg: string
}

export function usePlantIdentification(onIdentified?: () => void): UsePlantIdentificationReturn {
  const [isProcessing, setIsProcessing] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  const identify = useCallback(async (
    video: HTMLVideoElement,
    canvas: HTMLCanvasElement,
    organ: string,
  ) => {
    setIsProcessing(true)
    setErrorMsg('')

    try {
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        setErrorMsg('無法初始化影像擷取工具')
        return
      }
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

      const blob = await new Promise<Blob | null>((resolve) => {
        canvas.toBlob(resolve, 'image/jpeg', 0.8)
      })
      if (!blob) {
        setErrorMsg('無法擷取影像')
        return
      }

      const reader = new FileReader()
      const base64data = await new Promise<string>((resolve, reject) => {
        reader.onloadend = () => resolve(reader.result as string)
        reader.onerror = reject
        reader.readAsDataURL(blob)
      })

      const result = await identifyPlant(blob, organ)
      const topMatch = result?.results?.[0]
      const commonName = topMatch?.species?.commonNames?.[0]
        || topMatch?.species?.scientificNameWithoutAuthor
        || 'Unknown'

      await savePokedexEntry({
        id: Date.now().toString(),
        name: commonName,
        type: 'plant',
        metadata: result,
        timestamp: Date.now(),
      }, base64data)

      onIdentified?.()
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : '辨識失敗，請重試')
    } finally {
      setIsProcessing(false)
    }
  }, [onIdentified])

  return { identify, isProcessing, errorMsg }
}
