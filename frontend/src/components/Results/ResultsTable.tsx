import type { QueryResults } from '../../types'

interface Props {
  results: QueryResults
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
              {row.map((cell, j) => <td key={j}>{cell ?? '—'}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
