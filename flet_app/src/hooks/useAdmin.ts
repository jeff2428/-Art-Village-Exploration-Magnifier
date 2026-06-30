import { useCallback, useEffect, useState } from 'react'
import { fetchAnimals, authAdmin, updateAnimals } from '../services/api'
import type { Animal } from '../types'

export interface UseAdminReturn {
  password: string
  setPassword: (p: string) => void
  isAuthenticated: boolean
  animals: Animal[]
  loading: boolean
  message: string
  login: () => Promise<void>
  save: () => Promise<void>
  addAnimal: () => void
  removeAnimal: (index: number) => void
  updateAnimal: (index: number, field: 'name' | 'emoji' | 'role' | 'desc', value: string) => void
}

export function useAdmin(): UseAdminReturn {
  const [password, setPassword] = useState('')
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [animals, setAnimals] = useState<Animal[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!isAuthenticated) return
    fetchAnimals()
      .then((data) => { if (data?.animals) setAnimals(data.animals) })
      .catch(() => setMessage('載入動物資料失敗'))
  }, [isAuthenticated])

  const login = useCallback(async () => {
    setLoading(true)
    setMessage('')
    try {
      const ok = await authAdmin(password)
      if (ok) {
        setIsAuthenticated(true)
      } else {
        setMessage('密碼錯誤')
      }
    } catch {
      setMessage('驗證失敗')
    } finally {
      setLoading(false)
    }
  }, [password])

  const save = useCallback(async () => {
    setLoading(true)
    setMessage('')
    try {
      await updateAnimals(animals, password)
      setMessage('保存成功！')
    } catch (err) {
      setMessage(`保存失敗: ${err instanceof Error ? err.message : '未知錯誤'}`)
    } finally {
      setLoading(false)
    }
  }, [animals, password])

  const addAnimal = useCallback(() => {
    setAnimals((prev) => [
      ...prev,
      { name: '新動物', type: 'animal', emoji: '🐾', role: '', desc: '', portrait: '', photos: [] },
    ])
  }, [])

  const removeAnimal = useCallback((index: number) => {
    setAnimals((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const updateAnimal = useCallback((index: number, field: 'name' | 'emoji' | 'role' | 'desc', value: string) => {
    setAnimals((prev) => prev.map((a, i) => (i === index ? { ...a, [field]: value } : a)))
  }, [])

  return {
    password, setPassword,
    isAuthenticated,
    animals,
    loading, message,
    login, save,
    addAnimal, removeAnimal, updateAnimal,
  }
}
