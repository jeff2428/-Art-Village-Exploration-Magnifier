import { useAdmin } from '../hooks/useAdmin'
import './Admin.css'

export default function Admin() {
  const {
    password, setPassword,
    isAuthenticated,
    animals,
    loading, message,
    login, save,
    addAnimal, removeAnimal, updateAnimal,
  } = useAdmin()

  if (!isAuthenticated) {
    return (
      <div className="admin-container glass-panel">
        <h2>管理員登入</h2>
        <form onSubmit={(e) => { e.preventDefault(); login() }} className="admin-login-form">
          <input
            type="password"
            placeholder="請輸入管理員密碼"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
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
        <button onClick={() => { window.location.href = '/' }} className="btn">返回首頁</button>
      </header>

      {message && <p className={`admin-message ${message.includes('成功') ? 'success' : 'error'}`}>{message}</p>}

      <div className="admin-animals-list">
        {animals.map((animal, i) => (
          <div key={i} className="admin-animal-card">
            <div className="admin-animal-header">
              <h3>{animal.name || '未命名'}</h3>
              <button onClick={() => removeAnimal(i)} className="btn danger-btn btn-small">刪除</button>
            </div>
            <div className="admin-form-group">
              <label>名稱</label>
              <input type="text" value={animal.name} onChange={(e) => updateAnimal(i, 'name', e.target.value)} className="admin-input" />
            </div>
            <div className="admin-form-group">
              <label>表情符號 (Emoji)</label>
              <input type="text" value={animal.emoji} onChange={(e) => updateAnimal(i, 'emoji', e.target.value)} className="admin-input" />
            </div>
            <div className="admin-form-group">
              <label>角色 (Role)</label>
              <input type="text" value={animal.role} onChange={(e) => updateAnimal(i, 'role', e.target.value)} className="admin-input" />
            </div>
            <div className="admin-form-group">
              <label>介紹 (Description)</label>
              <textarea value={animal.desc} onChange={(e) => updateAnimal(i, 'desc', e.target.value)} className="admin-input admin-textarea" />
            </div>
          </div>
        ))}
      </div>

      <div className="admin-actions">
        <button onClick={addAnimal} className="btn primary-btn">新增動物</button>
        <button onClick={save} className="btn success-btn" disabled={loading}>
          {loading ? '保存中...' : '儲存變更'}
        </button>
      </div>
    </div>
  )
}
