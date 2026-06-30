import type { FilterType } from '../hooks/usePokedex'

interface FilterTabsProps {
  filter: FilterType
  onChange: (f: FilterType) => void
}

const TABS: { value: FilterType; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'plant', label: '植物' },
  { value: 'animal', label: '動物' },
]

export default function FilterTabs({ filter, onChange }: FilterTabsProps) {
  return (
    <div className="filter-tabs">
      {TABS.map(({ value, label }) => (
        <button
          key={value}
          className={`tab ${filter === value ? 'active' : ''}`}
          onClick={() => onChange(value)}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
