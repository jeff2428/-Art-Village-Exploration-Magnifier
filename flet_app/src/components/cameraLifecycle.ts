export function stopMediaStream(stream: MediaStream | null): void {
  stream?.getTracks().forEach((track) => track.stop())
}

export function prepareCapture(
  video: HTMLVideoElement,
  canvas: HTMLCanvasElement,
): CanvasRenderingContext2D | null {
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  return canvas.getContext('2d')
}
