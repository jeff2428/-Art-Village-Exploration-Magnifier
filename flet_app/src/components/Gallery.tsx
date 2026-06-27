import React, { useEffect, useState } from 'react'
import { getPokedexEntries, PokedexEntry, getImage } from '../services/storage'
import { fetchAnimals } from '../services/api'
import './Gallery.css'

interface GalleryProps {
  onClose: () => void
}

export default function Gallery({ onClose }: GalleryProps) {
  const [entries, setEntries] = useState<PokedexEntry[]>([])
  const [animals, setAnimals] = useState<any[]>([])
  const [filter, setFilter] = useState<'all' | 'plant' | 'animal'>('all')
  const [selectedEntry, setSelectedEntry] = useState<PokedexEntry | null>(null)
  
  useEffect(() => {
    async function loadData() {
      const dbEntries = await getPokedexEntries()
      setEntries(dbEntries)
      
      try {
        const animalData = await fetchAnimals()
        if (animalData?.animals) {
          setAnimals(animalData.animals)
        }
      } catch (err) {
        console.error('Failed to fetch animals', err)
      }
    }
    loadData()
  }, [])

  const displayEntries = entries.filter(e => filter === 'all' || e.type === filter)

  return (
    <div className="gallery-container">
      <header className="gallery-header">
        <h2>探險圖鑑</h2>
        <button className="btn close-btn" onClick={onClose}>返回相機</button>
      </header>

      <div className="filter-tabs">
        <button className={`tab ${filter === 'all' ? 'active' : ''}`} onClick={() => setFilter('all')}>全部</button>
        <button className={`tab ${filter === 'plant' ? 'active' : ''}`} onClick={() => setFilter('plant')}>植物</button>
        <button className={`tab ${filter === 'animal' ? 'active' : ''}`} onClick={() => setFilter('animal')}>動物</button>
      </div>

      <div className="gallery-grid">
        {filter !== 'plant' && animals.map((animal, i) => (
          <div key={`animal-${i}`} className="gallery-card animal-card glass-panel">
            <div className="emoji-avatar">{animal.emoji}</div>
            <div className="card-info">
              <h3>{animal.name}</h3>
              <p>{animal.role}</p>
            </div>
          </div>
        ))}

        {displayEntries.map(entry => (
          <GalleryCard key={entry.id} entry={entry} onClick={() => setSelectedEntry(entry)} />
        ))}

        {displayEntries.length === 0 && (filter === 'all' || filter === 'plant') && (
          <div className="empty-state">
            <p>目前還沒有收集到植物喔！</p>
            <p>趕快去探索吧 🌿</p>
          </div>
        )}
      </div>

      {selectedEntry && (
        <DetailModal entry={selectedEntry} onClose={() => setSelectedEntry(null)} />
      )}
    </div>
  )
}

function GalleryCard({ entry, onClick }: { entry: PokedexEntry, onClick: () => void }) {
  const [imgSrc, setImgSrc] = useState<string>('')

  useEffect(() => {
    if (entry.captured_image) {
      getImage(entry.captured_image).then(src => {
        if (src) setImgSrc(src)
      })
    }
  }, [entry.captured_image])

  return (
    <div className="gallery-card glass-panel" onClick={onClick}>
      {imgSrc ? (
        <img src={imgSrc} alt={entry.name} className="card-img" />
      ) : (
        <div className="card-img placeholder">🌿</div>
      )}
      <div className="card-info">
        <h3>{entry.name}</h3>
      </div>
    </div>
  )
}

function DetailModal({ entry, onClose }: { entry: PokedexEntry, onClose: () => void }) {
  const [imgSrc, setImgSrc] = useState<string>('')

  useEffect(() => {
    if (entry.captured_image) {
      getImage(entry.captured_image).then(src => {
        if (src) setImgSrc(src)
      })
    }
  }, [entry.captured_image])

  const perenual = entry.metadata?.perenual
  const careLevel = perenual?.care_level ? `照護難度: ${perenual.care_level}` : ''
  const isPoisonous = perenual?.poisonous_to_humans ? '⚠️ 有毒 (對人類)' : (perenual?.poisonous_to_humans === false ? '✅ 無毒' : '')

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content glass-panel" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>✕</button>
        {imgSrc && <img src={imgSrc} alt={entry.name} className="modal-img" />}
        <h2>{entry.name}</h2>
        {perenual?.scientific_name && <p className="scientific-name">{perenual.scientific_name}</p>}
        
        <div className="modal-details">
          {careLevel && <span className="tag">{careLevel}</span>}
          {isPoisonous && <span className="tag warning">{isPoisonous}</span>}
          {perenual?.cycle && <span className="tag">{perenual.cycle}</span>}
        </div>
        
        {perenual?.description && (
          <p className="description">{perenual.description}</p>
        )}
      </div>
    </div>
  )
}
