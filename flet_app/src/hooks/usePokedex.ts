import { useEffect, useState } from 'react'
import { getPokedexEntries } from '../services/storage'
import { fetchAnimals } from '../services/api'
import type { PokedexEntry, Animal } from '../types'

export type FilterType = 'all' | 'plant' | 'animal'

export interface UsePokedexReturn {
  entries: PokedexEntry[]
  animals: Animal[]
  filter: FilterType
  setFilter: (f: FilterType) => void
  loading: boolean
  filteredEntries: PokedexEntry[]
}

export function usePokedex(): UsePokedexReturn {
  const [entries, setEntries] = useState<PokedexEntry[]>([])
  const [animals, setAnimals] = useState<Animal[]>([])
  const [filter, setFilter] = useState<FilterType>('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      setLoading(true)
      const [dbEntries, animalData] = await Promise.all([
        getPokedexEntries(),
        fetchAnimals().catch(() => ({ animals: [] })),
      ])
      setEntries(dbEntries)
      setAnimals(animalData.animals)
      setLoading(false)
    }
    loadData()
  }, [])

  const filteredEntries = entries.filter((e) => filter === 'all' || e.type === filter)

  return { entries, animals, filter, setFilter, loading, filteredEntries }
}
