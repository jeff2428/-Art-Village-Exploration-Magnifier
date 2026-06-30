import {
  FlowerLotus,
  Leaf,
  Orange,
  Sparkle,
  Tree,
} from '@phosphor-icons/react'

const ORGAN_OPTIONS = [
  { value: 'auto', label: '自動', Icon: Sparkle },
  { value: 'leaf', label: '葉', Icon: Leaf },
  { value: 'flower', label: '花', Icon: FlowerLotus },
  { value: 'fruit', label: '果', Icon: Orange },
  { value: 'bark', label: '樹皮', Icon: Tree },
] as const

interface OrganSelectorProps {
  organ: string
  onSelect: (value: string) => void
  disabled?: boolean
}

export default function OrganSelector({ organ, onSelect, disabled }: OrganSelectorProps) {
  return (
    <section className="capture-panel" aria-labelledby="capture-organ-title">
      <h1 id="capture-organ-title">拍攝部位</h1>
      <div className="organ-segments" role="group" aria-label="拍攝部位">
        {ORGAN_OPTIONS.map(({ value, label, Icon }) => {
          const isSelected = organ === value
          return (
            <button
              type="button"
              key={value}
              className={`organ-segment ${isSelected ? 'is-selected' : ''}`}
              onClick={() => onSelect(value)}
              disabled={disabled}
              aria-pressed={isSelected}
              aria-label={label}
            >
              <Icon size={22} weight={isSelected ? 'fill' : 'bold'} aria-hidden="true" />
              <span>{label}</span>
            </button>
          )
        })}
      </div>
    </section>
  )
}
