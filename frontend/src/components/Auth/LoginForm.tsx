import { useState } from 'react'

interface Props {
  onLogin: (username: string, password: string) => Promise<void>
  onSwitchToRegister: () => void
}

export function LoginForm({ onLogin, onSwitchToRegister }: Props) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await onLogin(username, password)
    } catch {
      setError('Invalid username or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-card">
      <div className="auth-brand">
        <div className="auth-brand-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <ellipse cx="12" cy="5" rx="9" ry="3" />
            <path d="M3 5v14c0 1.657 4.03 3 9 3s9-1.343 9-3V5" />
            <path d="M3 12c0 1.657 4.03 3 9 3s9-1.343 9-3" />
          </svg>
        </div>
        <span className="auth-brand-name">NaturalQuery</span>
      </div>
      <h2>Sign in to your account</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Username</label>
          <input value={username} onChange={e => setUsername(e.target.value)} required placeholder="your_username" />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="••••••••" />
        </div>
        {error && <p className="error-msg">{error}</p>}
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
      <p className="auth-footer">
        No account?{' '}
        <button className="link-btn" onClick={onSwitchToRegister}>Register</button>
      </p>
    </div>
  )
}
