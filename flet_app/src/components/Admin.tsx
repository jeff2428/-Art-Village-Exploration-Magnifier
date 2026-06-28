import { useState, useEffect } from 'react'
import { fetchAnimals, API_URL, type Animal } from '../services/api'
import './Admin.css'

export default function Admin() {
  const [password, setPassword] = useState('')
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [animals, setAnimals] = useState<Animal[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (isAuthenticated) {
      loadAnimals()
    }
  }, [isAuthenticated])

  async function loadAnimals() {
    try {
      const data = await fetchAnimals()
      if (data?.animals) {
        setAnimals(data.animals)
      }
    } catch (err) {
      console.error(err)
      setMessage('載入動物資料失敗')
    }
  }

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setMessage('')
    try {
      const res = await fetch(`${API_URL}/animals/auth`, {
        method: 'POST',
        headers: {
          'X-Admin-Password': password,
        },
      })
      const data = await res.json()
      if (data.ok) {
        setIsAuthenticated(true)
      } else {
        setMessage('密碼錯誤')
      }
    } catch (err) {
      console.error(err)
      setMessage('驗證失敗')
    } finally {
      setLoading(false)
    }
  }

  async function handleSave() {
    setLoading(true)
    setMessage('')
    try {
      const res = await fetch(`${API_URL}/animals`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Password': password,
        },
        body: JSON.stringify({ animals }),
      })
      const data = await res.json()
      if (res.ok && !data.error) {
        setMessage('保存成功！')
      } else {
        setMessage(`保存失敗: ${data.error || '未知錯誤'}`)
      }
    } catch (err) {
      console.error(err)
      setMessage('保存時發生錯誤')
    } finally {
      setLoading(false)
    }
  }

  function handleAddAnimal() {
    setAnimals([...animals, { name: '新動物', type: 'animal', emoji: '🐾', role: '', desc: '', portrait: '', photos: [] }])
  }

  function handleRemoveAnimal(index: number) {
    const newAnimals = [...animals]
    newAnimals.splice(index, 1)
    setAnimals(newAnimals)
  }

  function handleUpdateAnimal(index: number, field: 'name' | 'emoji' | 'role' | 'desc', value: string) {
    const newAnimals = [...animals]
    newAnimals[index] = { ...newAnimals[index], [field]: value }
    setAnimals(newAnimals)
  }

  if (!isAuthenticated) {
    return (
      <div className="admin-container glass-panel">
        <h2>管理員登入</h2>
        <form onSubmit={handleLogin} className="admin-login-form">
          <input
            type="password"
            placeholder="請輸入管理員密碼"
            value={password}
            onChange={e => setPassword(e.target.value)}
            disabled={loading}
            className="admin-input"
          />
          <button type="submit" className="btn primary-btn" disabled={loading}>登入</button>
        </form>
        {message && <p className="admin-message error">{message}</p>}
      </div>
    )
  }

  return (
    <div className="admin-container glass-panel">
      <header className="admin-header">
        <h2>動物名單管理</h2>
        <button onClick={() => window.location.href = '/'} className="btn">返回首頁</button>
      </header>
      
      {message && <p className={`admin-message ${message.includes('成功') ? 'success' : 'error'}`}>{message}</p>}
      
      <div className="admin-animals-list">
        {animals.map((animal, i) => (
          <div key={i} className="admin-animal-card">
            <div className="admin-animal-header">
              <h3>{animal.name || '未命名'}</h3>
              <button onClick={() => handleRemoveAnimal(i)} className="btn danger-btn btn-small">刪除</button>
            </div>
            <div className="admin-form-group">
              <label>名稱</label>
              <input type="text" value={animal.name} onChange={e => handleUpdateAnimal(i, 'name', e.target.value)} className="admin-input" />
            </div>
            <div className="admin-form-group">
              <label>表情符號 (Emoji)</label>
              <input type="text" value={animal.emoji} onChange={e => handleUpdateAnimal(i, 'emoji', e.target.value)} className="admin-input" />
            </div>
            <div className="admin-form-group">
              <label>角色 (Role)</label>
              <input type="text" value={animal.role} onChange={e => handleUpdateAnimal(i, 'role', e.target.value)} className="admin-input" />
            </div>
            <div className="admin-form-group">
              <label>介紹 (Description)</label>
              <textarea value={animal.desc} onChange={e => handleUpdateAnimal(i, 'desc', e.target.value)} className="admin-input admin-textarea" />
            </div>
          </div>
        ))}
      </div>

      <div className="admin-actions">
        <button onClick={handleAddAnimal} className="btn primary-btn">新增動物</button>
        <button onClick={handleSave} className="btn success-btn" disabled={loading}>
          {loading ? '保存中...' : '儲存變更'}
        </button>
      </div>
    </div>
  )
}
