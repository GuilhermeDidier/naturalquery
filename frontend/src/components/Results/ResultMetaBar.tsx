// frontend/src/components/Results/ResultMetaBar.tsx
interface Props {
  rowCount: number
  sql: string
}

export function ResultMetaBar({ rowCount, sql }: Props) {
  function handleCopy() {
    navigator.clipboard.writeText(sql).catch(() => {})
  }

  return (
    <div className="result-meta-bar">
      <span className="row-badge">↗ {rowCount} {rowCount === 1 ? 'row' : 'rows'}</span>
      <button className="copy-sql-btn" onClick={handleCopy}>Copy SQL</button>
    </div>
  )
}
