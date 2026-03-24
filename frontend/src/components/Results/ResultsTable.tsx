import type { QueryResults } from '../../types'

interface Props {
  results: QueryResults
}

const MONEY_KEYWORDS = ['revenue', 'total', 'price', 'spend', 'sales', 'amount', 'income', 'profit', 'cost']

function isMoney(col: string) {
  const lower = col.toLowerCase()
  return MONEY_KEYWORDS.some(k => lower.includes(k))
}

function formatCell(value: unknown, col: string): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'number') {
    if (isMoney(col)) {
      return '$' + value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }
    return Number.isInteger(value) ? String(value) : parseFloat(value.toFixed(2)).toString()
  }
  return String(value)
}

export function ResultsTable({ results }: Props) {
  if (!results.rows.length) {
    return <p style={{ color: '#4b5563', fontSize: 13 }}>No results found.</p>
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {results.columns.map(col => <th key={col}>{col}</th>)}
          </tr>
        </thead>
        <tbody>
          {results.rows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td key={j}>{formatCell(cell, results.columns[j])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
