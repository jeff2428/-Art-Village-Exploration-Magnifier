import type { Animal } from '../types'

interface AnimalModalProps {
  animal: Animal
  onClose: () => void
}

export default function AnimalModal({ animal, onClose }: AnimalModalProps) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content glass-panel animal-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>✕</button>
        <div className="modal-emoji-avatar">{animal.emoji}</div>
        <h2 className="modal-animal-name">{animal.name}</h2>
        <p className="modal-animal-role">{animal.role}</p>
        <p className="description">{animal.desc}</p>
      </div>
    </div>
  )
}
