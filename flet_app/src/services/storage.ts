import { openDB, DBSchema, IDBPDatabase } from 'idb'
import type { PlantIdentificationResult } from './api'

export interface PokedexEntry {
  id: string
  name: string
  type: 'plant' | 'animal'
  captured_image?: string // hash or data url
  metadata?: PlantIdentificationResult
  timestamp: number
}

interface AVDB extends DBSchema {
  pokedex: {
    key: string
    value: PokedexEntry
  }
  images: {
    key: string
    value: string // base64 or blob
  }
}

let dbPromise: Promise<IDBPDatabase<AVDB>> | null = null

export function initDB() {
  if (!dbPromise) {
    dbPromise = openDB<AVDB>('artVillageDB', 1, {
      upgrade(db) {
        db.createObjectStore('pokedex', { keyPath: 'id' })
        db.createObjectStore('images')
      }
    })
  }
  return dbPromise
}

export async function savePokedexEntry(entry: PokedexEntry, imageBase64?: string) {
  const db = await initDB()
  if (imageBase64) {
    const imgKey = `img_${entry.id}`
    await db.put('images', imageBase64, imgKey)
    entry.captured_image = imgKey
  }
  await db.put('pokedex', entry)
}

export async function getPokedexEntries(): Promise<PokedexEntry[]> {
  const db = await initDB()
  const entries = await db.getAll('pokedex')
  return entries.sort((a, b) => b.timestamp - a.timestamp)
}

export async function getImage(key: string): Promise<string | undefined> {
  if (!key.startsWith('img_')) return key // probably a direct url
  const db = await initDB()
  return db.get('images', key)
}
