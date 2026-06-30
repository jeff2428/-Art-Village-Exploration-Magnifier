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
  status?: string
  source?: string
  query?: string
  scientific_name?: string
  common_name?: string
  family?: string
  description?: string
  cycle?: string
  watering?: string
  sunlight?: string[]
  care_level?: string
  poisonous_to_humans?: boolean | null
  poisonous_to_pets?: boolean | null
  invasive?: boolean | null
}

export interface PlantSpecies {
  scientificNameWithoutAuthor?: string
  scientificName?: string
  commonNames?: string[]
}

export interface PlantResult {
  species?: PlantSpecies
  score?: number
}

export interface PlantIdentificationResult {
  results?: PlantResult[]
  perenual?: PerenualMetadata
  timing?: {
    plantnet_ms?: number
    perenual_ms?: number
    total_ms?: number
  }
}

export interface AnimalsResponse {
  animals: Animal[]
  source?: string
}

export interface PokedexEntry {
  id: string
  name: string
  type: 'plant' | 'animal'
  captured_image?: string
  metadata?: PlantIdentificationResult
  timestamp: number
}
