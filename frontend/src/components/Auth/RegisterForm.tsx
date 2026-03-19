import { useState } from 'react'

interface Props {
  onRegister: (username: string, email: string, password: string) => Promise<void>
  onSwitchToLogin: () => void
}

export function RegisterForm({ onRegister, onSwitchToLogin }: Props) {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await onRegister(username, email, password)
    } catch (err: any) {
      const data = err?.response?.data?.errors
      if (data?.username) setError(data.username[0])
      else if (data?.password) setError(data.password[0])
      else setError('Registration failed. Please try again.')
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
      <h2>Create your account</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Username</label>
          <input value={username} onChange={e => setUsername(e.target.value)} required placeholder="your_username" />
        </div>
        <div className="form-group">
          <label>Email</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="you@example.com" />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={6} placeholder="••••••••" />
        </div>
        {error && <p className="error-msg">{error}</p>}
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? 'Creating account...' : 'Create account'}
        </button>
      </form>
      <p className="auth-footer">
        Have an account?{' '}
        <button className="link-btn" onClick={onSwitchToLogin}>Sign in</button>
      </p>
    </div>
  )
}
