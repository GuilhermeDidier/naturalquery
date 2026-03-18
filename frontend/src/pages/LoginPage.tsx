import { useState } from 'react'
import { LoginForm } from '../components/Auth/LoginForm'
import { RegisterForm } from '../components/Auth/RegisterForm'

interface Props {
  onAuth: (token: string, username: string) => void
}

export function LoginPage({ onAuth }: Props) {
  const [mode, setMode] = useState<'login' | 'register'>('login')

  async function handleLogin(username: string, password: string) {
    const { login, setAuthToken } = await import('../api/client')
    const data = await login(username, password)
    setAuthToken(data.token)
    onAuth(data.token, data.username)
  }

  async function handleRegister(username: string, email: string, password: string) {
    const { register, setAuthToken } = await import('../api/client')
    const data = await register(username, email, password)
    setAuthToken(data.token)
    onAuth(data.token, data.username)
  }

  return (
    <div className="page-center">
      {mode === 'login' ? (
        <LoginForm onLogin={handleLogin} onSwitchToRegister={() => setMode('register')} />
      ) : (
        <RegisterForm onRegister={handleRegister} onSwitchToLogin={() => setMode('login')} />
      )}
    </div>
  )
}
