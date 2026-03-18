import type { HistoryItem } from '../../types'

interface Props {
  items: HistoryItem[]
  activeId: number | null
  onSelect: (item: HistoryItem) => void
}

export function QueryHistory({ items, activeId, onSelect }: Props) {
  return (
    <aside className="sidebar">
      <h3>History</h3>
      {items.length === 0 && (
        <p style={{ color: '#374151', fontSize: 12, marginTop: 8 }}>No queries yet</p>
      )}
      {items.map(item => (
        <div
          key={item.id}
          className={`history-item${activeId === item.id ? ' active' : ''}`}
          onClick={() => onSelect(item)}
          title={item.question}
        >
          {item.question}
        </div>
      ))}
    </aside>
  )
}
