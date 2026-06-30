import { useEffect, useState } from 'react'
import { getImage } from '../services/storage'
import type { PokedexEntry } from '../types'

interface PlantDetailModalProps {
  entry: PokedexEntry
  onClose: () => void
}

export default function PlantDetailModal({ entry, onClose }: PlantDetailModalProps) {
  const [imgSrc, setImgSrc] = useState<string>('')

  useEffect(() => {
    if (entry.captured_image) {
      getImage(entry.captured_image).then((src) => { if (src) setImgSrc(src) })
    }
  }, [entry.captured_image])

  const perenual = entry.metadata?.perenual
  const careLevel = perenual?.care_level ? `照護難度: ${perenual.care_level}` : ''
  const isPoisonous = perenual?.poisonous_to_humans
    ? '⚠️ 有毒 (對人類)'
    : perenual?.poisonous_to_humans === false ? '✅ 無毒' : ''

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content glass-panel" onClick={(e) => e.stopPropagation()}>
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
