// In production, this will be / 
// In dev, we can proxy or set the env var
export const API_URL = import.meta.env.VITE_API_URL || ''

export async function identifyPlant(imageBlob: Blob, organ: string = 'auto') {
  const formData = new FormData()
  formData.append('images', imageBlob, 'capture.jpg')
  if (organ !== 'auto') {
    formData.append('organs', organ)
  }

  const res = await fetch(`${API_URL}/`, {
    method: 'POST',
    body: formData
  })

  if (!res.ok) {
    throw new Error(`API Error: ${res.statusText}`)
  }

  return res.json()
}

export async function fetchAnimals() {
  const res = await fetch(`${API_URL}/animals`)
  if (!res.ok) return { animals: [] }
  return res.json()
}
