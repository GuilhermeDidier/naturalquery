export interface AuthResponse {
  token: string
  user_id: number
  username: string
}

export interface QueryResults {
  columns: string[]
  rows: (string | number | null)[][]
}

export interface ChartConfig {
  type: 'bar' | 'line' | 'pie'
  x_key: string
  y_key: string
  label: string
}

export interface QueryResponse {
  question: string
  sql_generated: string
  explanation: string
  results: QueryResults
  chart_config: ChartConfig | null
  row_count: number
}

export interface HistoryItem {
  id: number
  question: string
  sql_generated: string
  explanation: string
  results: QueryResults
  chart_config: ChartConfig | null
  row_count: number
  created_at: string
}
