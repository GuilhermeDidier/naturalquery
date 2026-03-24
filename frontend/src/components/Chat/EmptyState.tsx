// frontend/src/components/Chat/EmptyState.tsx
import { AIBadge } from '../UI/AIBadge'

interface Props {
  onSelect: (question: string) => void
}

const QUERY_CARDS = [
  { icon: '📦', question: 'Top 5 best-selling products' },
  { icon: '📦', question: 'Products with low stock' },
  { icon: '💰', question: 'Monthly revenue trend' },
  { icon: '💰', question: 'Revenue by category' },
  { icon: '👤', question: 'Top 10 customers by spend' },
  { icon: '👤', question: 'Customers by state' },
]

export function EmptyState({ onSelect }: Props) {
  return (
    <div className="empty-state">
      <AIBadge />
      <p className="empty-state-heading">What do you want to know?</p>
      <p className="empty-state-subtitle">Ask in plain English. I'll handle the SQL.</p>
      <div className="query-cards-grid">
        {QUERY_CARDS.map(({ icon, question }) => (
          <button
            key={question}
            className="query-card"
            onClick={() => onSelect(question)}
          >
            <span className="query-card-icon">{icon}</span>
            <span className="query-card-text">{question}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
