import { describe, expect, it, vi } from 'vitest'
import { prepareCapture, stopMediaStream } from './cameraLifecycle'

describe('stopMediaStream', () => {
  it('stops every track owned by the stream', () => {
    const firstTrack = { stop: vi.fn() }
    const secondTrack = { stop: vi.fn() }
    const stream = {
      getTracks: () => [firstTrack, secondTrack],
    } as unknown as MediaStream

    stopMediaStream(stream)

    expect(firstTrack.stop).toHaveBeenCalledOnce()
    expect(secondTrack.stop).toHaveBeenCalledOnce()
  })

  it('accepts an absent stream during cleanup', () => {
    expect(() => stopMediaStream(null)).not.toThrow()
  })
})

describe('prepareCapture', () => {
  it('returns null when the browser cannot provide a canvas context', () => {
    const video = { videoWidth: 640, videoHeight: 480 } as HTMLVideoElement
    const canvas = {
      width: 0,
      height: 0,
      getContext: vi.fn(() => null),
    } as unknown as HTMLCanvasElement

    expect(prepareCapture(video, canvas)).toBeNull()
    expect(canvas.width).toBe(640)
    expect(canvas.height).toBe(480)
  })
})
