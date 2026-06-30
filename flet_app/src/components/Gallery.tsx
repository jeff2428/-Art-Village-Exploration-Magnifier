import { useState } from 'react'
import { getImage } from '../services/storage'
import { usePokedex } from '../hooks/usePokedex'
import type { PokedexEntry, Animal } from '../types'
import PlantDetailModal from './PlantDetailModal'
import AnimalModal from './AnimalModal'
import FilterTabs from './FilterTabs'
import './Gallery.css'

interface GalleryProps {
  onClose: () => void
}

export default function Gallery({ onClose }: GalleryProps) {
  const { animals, filter, setFilter, loading, filteredEntries } = usePokedex()
  const [selectedEntry, setSelectedEntry] = useState<PokedexEntry | null>(null)
  const [selectedAnimal, setSelectedAnimal] = useState<Animal | null>(null)

  return (
    <div className="gallery-container">
      <header className="gallery-header">
        <h2>探險圖鑑</h2>
        <button className="btn close-btn" onClick={onClose}>返回相機</button>
      </header>

      <FilterTabs filter={filter} onChange={setFilter} />

      <div className="gallery-grid">
        {filter !== 'plant' && animals.map((animal, i) => (
          <div key={`animal-${i}`} className="gallery-card animal-card glass-panel" onClick={() => setSelectedAnimal(animal)}>
            <div className="emoji-avatar">{animal.emoji}</div>
            <div className="card-info">
              <h3>{animal.name}</h3>
              <p>{animal.role}</p>
            </div>
          </div>
        ))}

        {filteredEntries.map((entry) => (
          <GalleryCard key={entry.id} entry={entry} onClick={() => setSelectedEntry(entry)} />
        ))}

        {!loading && filteredEntries.length === 0 && (filter === 'all' || filter === 'plant') && (
          <div className="empty-state">
            <p>目前還沒有收集到植物喔！</p>
            <p>趕快去探索吧 🌿</p>
          </div>
        )}
      </div>

      {selectedEntry && (
        <PlantDetailModal entry={selectedEntry} onClose={() => setSelectedEntry(null)} />
      )}

      {selectedAnimal && (
        <AnimalModal animal={selectedAnimal} onClose={() => setSelectedAnimal(null)} />
      )}
    </div>
  )
}

function GalleryCard({ entry, onClick }: { entry: PokedexEntry; onClick: () => void }) {
  const [imgSrc, setImgSrc] = useState<string>('')

  if (entry.captured_image && !imgSrc) {
    getImage(entry.captured_image).then((src) => { if (src) setImgSrc(src) })
  }

  return (
    <div className="gallery-card glass-panel" onClick={onClick}>
      {imgSrc ? (
        <img src={imgSrc} alt={entry.name} className="card-img" loading="lazy" />
      ) : (
        <div className="card-img placeholder">🌿</div>
      )}
      <div className="card-info">
        <h3>{entry.name}</h3>
      </div>
    </div>
  )
}
