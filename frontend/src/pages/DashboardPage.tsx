import { useState, useEffect } from 'react'
import { Header } from '../components/Layout/Header'
import { QueryHistory as QueryHistorySidebar } from '../components/Sidebar/QueryHistory'
import { ChatInput } from '../components/Chat/ChatInput'
import { ResultsTable } from '../components/Results/ResultsTable'
import { ChartDisplay } from '../components/Results/ChartDisplay'
import { postQuery, getHistory } from '../api/client'
import type { QueryResponse, HistoryItem } from '../types'

interface Props {
  username: string
  onLogout: () => void
}

export function DashboardPage({ username, onLogout }: Props) {
  const [result, setResult] = useState<QueryResponse | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getHistory().then(setHistory).catch(() => {})
  }, [])

  async function handleQuery(question: string) {
    setLoading(true)
    setError('')
    try {
      const data = await postQuery(question)
      setResult(data)
      const h = await getHistory()
      setHistory(h)
      if (h.length > 0) setActiveId(h[0].id)
    } catch (err: any) {
      const errors = err?.response?.data?.errors
      if (errors?.question) setError(errors.question[0])
      else if (errors?.query) setError(errors.query[0])
      else setError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  function handleHistorySelect(item: HistoryItem) {
    setActiveId(item.id)
    setResult({
      question: item.question,
      sql_generated: item.sql_generated,
      explanation: item.explanation,
      results: item.results,
      chart_config: item.chart_config,
      row_count: item.row_count,
    })
  }

  return (
    <div className="dashboard">
      <Header username={username} onLogout={onLogout} />
      <div className="dashboard-body">
        <QueryHistorySidebar items={history} activeId={activeId} onSelect={handleHistorySelect} />
        <div className="main-area">
          <div className="results-area">
            {!result && !loading && (
              <div className="empty-state">
                <p>Ask a question about the store data to get started.</p>
                <p style={{ fontSize: 12 }}>Example: "What are the top 5 best selling products?"</p>
              </div>
            )}
            {loading && <p className="loading-text">Thinking...</p>}
            {error && <p className="error-msg" style={{ padding: '8px 0' }}>{error}</p>}
            {result && !loading && (
              <>
                <div className="explanation-box">{result.explanation}</div>
                <ResultsTable results={result.results} />
                {result.chart_config && (
                  <ChartDisplay config={result.chart_config} results={result.results} />
                )}
                <details className="sql-toggle">
                  <summary>View generated SQL</summary>
                  <pre className="sql-block">{result.sql_generated}</pre>
                </details>
              </>
            )}
          </div>
          <ChatInput onSubmit={handleQuery} disabled={loading} />
        </div>
      </div>
    </div>
  )
}
