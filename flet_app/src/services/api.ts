import type { Animal, PlantIdentificationResult, AnimalsResponse, PerenualMetadata } from '../types'

const DEFAULT_API_URL = 'https://art-village-magnifier.jeff2428.workers.dev'
export const API_URL = import.meta.env.VITE_API_URL?.replace(/\/$/, '') || DEFAULT_API_URL

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error((body as { error?: string }).error || `API Error: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export async function identifyPlant(imageBlob: Blob, organ: string = 'auto'): Promise<PlantIdentificationResult> {
  const formData = new FormData()
  formData.append('images', imageBlob, 'capture.jpg')
  if (organ !== 'auto') {
    formData.append('organs', organ)
  }
  return request<PlantIdentificationResult>(`${API_URL}/`, { method: 'POST', body: formData })
}

export async function fetchAnimals(): Promise<AnimalsResponse> {
  const res = await fetch(`${API_URL}/animals`)
  if (!res.ok) return { animals: [] }
  return res.json() as Promise<AnimalsResponse>
}

export async function fetchPlantMetadata(scientificName: string): Promise<PerenualMetadata> {
  return request<PerenualMetadata>(`${API_URL}/metadata?scientificName=${encodeURIComponent(scientificName)}`)
}

export async function authAdmin(password: string): Promise<boolean> {
  const res = await fetch(`${API_URL}/animals/auth`, {
    method: 'POST',
    headers: { 'X-Admin-Password': password },
  })
  const data = (await res.json()) as { ok: boolean }
  return data.ok
}

export async function updateAnimals(animals: Animal[], password: string): Promise<AnimalsResponse> {
  return request<AnimalsResponse>(`${API_URL}/animals`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'X-Admin-Password': password,
    },
    body: JSON.stringify({ animals }),
  })
}

export type { Animal, PlantIdentificationResult, AnimalsResponse, PerenualMetadata }
