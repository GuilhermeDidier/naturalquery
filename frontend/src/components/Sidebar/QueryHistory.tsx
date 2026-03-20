import type { HistoryItem } from '../../types'

interface Props {
  items: HistoryItem[]
  activeId: number | null
  onSelect: (item: HistoryItem) => void
}

function formatRelativeTime(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime()
  const minutes = Math.floor(diff / 60_000)
  const hours = Math.floor(diff / 3_600_000)
  const days = Math.floor(diff / 86_400_000)

  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`
  if (hours < 24) return `${hours}h ago`
  if (days === 1) return 'Yesterday'

  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' }).format(
    new Date(isoString)
  )
}

function ChartIcon() {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
    >
      <rect x="1" y="7" width="2" height="4" />
      <rect x="5" y="4" width="2" height="7" />
      <rect x="9" y="1" width="2" height="10" />
    </svg>
  )
}

export function QueryHistory({ items, activeId, onSelect }: Props) {
  return (
    <aside className="sidebar">
      <h3>History · {items.length} {items.length === 1 ? 'query' : 'queries'}</h3>
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
          <span className="history-item-question">{item.question}</span>
          <span className="history-item-meta">
            <span>{formatRelativeTime(item.created_at)}</span>
            {item.row_count != null && (
              <span className="history-item-rows">{item.row_count} rows</span>
            )}
            {item.chart_config && (
              <span className="history-chart-icon"><ChartIcon /></span>
            )}
          </span>
        </div>
      ))}
    </aside>
  )
}
