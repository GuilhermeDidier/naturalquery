import { useState } from 'react'

interface Props {
  onSubmit: (question: string) => void
  disabled: boolean
}

export function ChatInput({ onSubmit, disabled }: Props) {
  const [value, setValue] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const q = value.trim()
    if (!q) return
    onSubmit(q)
    setValue('')
  }

  return (
    <form className="chat-bar" onSubmit={handleSubmit}>
      <input
        value={value}
        onChange={e => setValue(e.target.value)}
        placeholder="Ask a question about the store data..."
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || !value.trim()}>
        {disabled ? '...' : 'Ask'}
      </button>
    </form>
  )
}
