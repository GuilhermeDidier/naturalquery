interface Props {
  onSelect: (question: string) => void
  disabled: boolean
}

const SUGGESTIONS = [
  'Top 5 best-selling products',
  'Products with low stock',
  'Monthly revenue trend',
  'Revenue by category',
  'Top 10 customers by spend',
  'Customers by state',
]

export function SuggestionChips({ onSelect, disabled }: Props) {
  return (
    <div className="suggestion-chips">
      {SUGGESTIONS.map(q => (
        <button
          key={q}
          className="suggestion-chip"
          onClick={() => onSelect(q)}
          disabled={disabled}
        >
          {q}
        </button>
      ))}
    </div>
  )
}
