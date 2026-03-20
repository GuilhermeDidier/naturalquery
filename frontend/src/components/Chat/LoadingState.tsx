// frontend/src/components/Chat/LoadingState.tsx
import { useState, useEffect } from 'react'
import { AIBadge } from '../UI/AIBadge'

const PHASES = [
  'Analyzing your question',
  'Generating SQL query',
  'Fetching results',
]

export function LoadingState() {
  const [phaseIndex, setPhaseIndex] = useState(0)

  useEffect(() => {
    const id = setInterval(() => {
      setPhaseIndex(i => (i + 1) % PHASES.length)
    }, 1500)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="loading-phase">
      <AIBadge />
      <span className="loading-phase-text">{PHASES[phaseIndex]}</span>
      <span className="loading-dots">
        <span>.</span>
        <span>.</span>
        <span>.</span>
      </span>
    </div>
  )
}
