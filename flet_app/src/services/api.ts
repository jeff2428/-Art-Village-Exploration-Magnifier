// In production, this will be / 
// In dev, we can proxy or set the env var
const DEFAULT_API_URL = 'https://art-village-magnifier.jeff2428.workers.dev'
export const API_URL = import.meta.env.VITE_API_URL?.replace(/\/$/, '') || DEFAULT_API_URL

export interface Animal {
  name: string
  type: 'animal'
  emoji: string
  role: string
  desc: string
  portrait: string
  photos: string[]
}

export interface PerenualMetadata {
  scientific_name?: string
  care_level?: string
  poisonous_to_humans?: boolean | null
  cycle?: string
  description?: string
}

export interface PlantIdentificationResult {
  results?: Array<{
    species?: {
      scientificNameWithoutAuthor?: string
      scientificName?: string
      commonNames?: string[]
    }
  }>
  perenual?: PerenualMetadata
}

interface AnimalsResponse {
  animals: Animal[]
  source?: string
}

export async function identifyPlant(imageBlob: Blob, organ: string = 'auto'): Promise<PlantIdentificationResult> {
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

export async function fetchAnimals(): Promise<AnimalsResponse> {
  const res = await fetch(`${API_URL}/animals`)
  if (!res.ok) return { animals: [] }
  return res.json() as Promise<AnimalsResponse>
}
