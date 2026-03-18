import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement, LineElement,
  PointElement, ArcElement, Title, Tooltip, Legend,
} from 'chart.js'
import { Bar, Line, Pie } from 'react-chartjs-2'
import type { ChartConfig, QueryResults } from '../../types'

ChartJS.register(
  CategoryScale, LinearScale, BarElement, LineElement,
  PointElement, ArcElement, Title, Tooltip, Legend
)

interface Props {
  config: ChartConfig
  results: QueryResults
}

const COLORS = ['#7c3aed','#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#84cc16']

export function ChartDisplay({ config, results }: Props) {
  const xIdx = results.columns.indexOf(config.x_key)
  const yIdx = results.columns.indexOf(config.y_key)

  if (xIdx === -1 || yIdx === -1) return null

  const labels = results.rows.map(r => String(r[xIdx]))
  const data = results.rows.map(r => Number(r[yIdx]))

  const chartData = {
    labels,
    datasets: [{
      label: config.label,
      data,
      backgroundColor: config.type === 'pie' ? COLORS : '#7c3aed',
      borderColor: config.type === 'line' ? '#7c3aed' : undefined,
      borderWidth: config.type === 'line' ? 2 : undefined,
      fill: false,
    }],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { color: '#94a3b8' } } },
    scales: config.type !== 'pie' ? {
      x: { ticks: { color: '#94a3b8' }, grid: { color: '#1e2433' } },
      y: { ticks: { color: '#94a3b8' }, grid: { color: '#1e2433' } },
    } : undefined,
  } as any

  return (
    <div className="chart-wrap">
      {config.type === 'bar' && <Bar data={chartData} options={options} style={{ height: '100%' }} />}
      {config.type === 'line' && <Line data={chartData} options={options} style={{ height: '100%' }} />}
      {config.type === 'pie' && <Pie data={chartData} options={options} style={{ height: '100%' }} />}
    </div>
  )
}
