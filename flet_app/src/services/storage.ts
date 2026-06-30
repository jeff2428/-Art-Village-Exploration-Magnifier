import { openDB, DBSchema, IDBPDatabase } from 'idb'
import type { PokedexEntry } from '../types'

interface AVDB extends DBSchema {
  pokedex: {
    key: string
    value: PokedexEntry
  }
  images: {
    key: string
    value: string
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

export async function savePokedexEntry(entry: PokedexEntry, imageBase64?: string): Promise<void> {
  try {
    const db = await initDB()
    if (imageBase64) {
      const imgKey = `img_${entry.id}`
      await db.put('images', imageBase64, imgKey)
      entry.captured_image = imgKey
    }
    await db.put('pokedex', entry)
  } catch (err) {
    console.error('Failed to save pokedex entry:', err)
  }
}

export async function getPokedexEntries(): Promise<PokedexEntry[]> {
  try {
    const db = await initDB()
    const entries = await db.getAll('pokedex')
    return entries.sort((a, b) => b.timestamp - a.timestamp)
  } catch (err) {
    console.error('Failed to read pokedex entries:', err)
    return []
  }
}

export async function deletePokedexEntry(id: string): Promise<void> {
  try {
    const db = await initDB()
    const entry = await db.get('pokedex', id)
    if (entry?.captured_image?.startsWith('img_')) {
      await db.delete('images', entry.captured_image)
    }
    await db.delete('pokedex', id)
  } catch (err) {
    console.error('Failed to delete pokedex entry:', err)
  }
}

export async function getImage(key: string): Promise<string | undefined> {
  if (!key.startsWith('img_')) return key
  try {
    const db = await initDB()
    return db.get('images', key)
  } catch (err) {
    console.error('Failed to get image:', err)
    return undefined
  }
}

export type { PokedexEntry }
