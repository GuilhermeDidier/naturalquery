import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { Header } from '../components/Layout/Header'
import { QueryHistory as QueryHistorySidebar } from '../components/Sidebar/QueryHistory'
import { ChatInput } from '../components/Chat/ChatInput'
import { ResultsTable } from '../components/Results/ResultsTable'
import { ChartDisplay } from '../components/Results/ChartDisplay'
import { EmptyState } from '../components/Chat/EmptyState'
import { LoadingState } from '../components/Chat/LoadingState'
import { SuggestionChips } from '../components/Chat/SuggestionChips'
import { ResultMetaBar } from '../components/Results/ResultMetaBar'
import { SqlBlock } from '../components/Results/SqlBlock'
import { AIBadge } from '../components/UI/AIBadge'
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
              <EmptyState onSelect={handleQuery} />
            )}
            {loading && <LoadingState />}
            {error && <p className="error-msg" style={{ padding: '8px 0' }}>{error}</p>}
            {result && !loading && (
              <>
                {/* 1. AI Response Card */}
                <div className="ai-response-card">
                  <div className="ai-response-header">
                    <AIBadge />
                    NaturalQuery AI
                  </div>
                  <div className="ai-response-text">
                    <ReactMarkdown>{result.explanation}</ReactMarkdown>
                  </div>
                </div>

                {/* 2. Result Meta Bar */}
                <ResultMetaBar rowCount={result.row_count} sql={result.sql_generated} />

                {/* 3. Chart (before table — insight first) */}
                {result.chart_config && (
                  <ChartDisplay config={result.chart_config} results={result.results} />
                )}

                {/* 4. Table */}
                <ResultsTable results={result.results} />

                {/* 5. SQL Block */}
                <SqlBlock sql={result.sql_generated} />
              </>
            )}
          </div>
          {result && <SuggestionChips onSelect={handleQuery} disabled={loading} />}
          <ChatInput onSubmit={handleQuery} disabled={loading} />
        </div>
      </div>
    </div>
  )
}
