import '@testing-library/jest-dom/vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import CameraView from './CameraView'

vi.mock('../hooks/useCamera', () => ({
  useCamera: () => ({
    videoRef: { current: null },
    canvasRef: { current: null },
    isReady: true,
    errorMsg: '',
    prepareCapture: vi.fn(() => ({})),
  }),
}))

vi.mock('../hooks/usePlantIdentification', () => ({
  usePlantIdentification: () => ({
    identify: vi.fn(),
    isProcessing: false,
    errorMsg: '',
  }),
}))

describe('CameraView controls', () => {
  beforeEach(() => {
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: {
        getUserMedia: vi.fn().mockResolvedValue({ getTracks: () => [] }),
      },
    })
  })

  it('offers accessible capture, gallery, and segmented organ controls', async () => {
    render(<CameraView onOpenGallery={vi.fn()} />)

    expect(await screen.findByRole('group', { name: '拍攝部位' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '拍照辨識' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '開啟圖鑑' })).toBeInTheDocument()

    const flowerButton = screen.getByRole('button', { name: '花' })
    fireEvent.click(flowerButton)
    expect(flowerButton).toHaveAttribute('aria-pressed', 'true')
  })
})
