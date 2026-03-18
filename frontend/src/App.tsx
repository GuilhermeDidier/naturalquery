import { useState, useEffect } from 'react'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { setAuthToken, loadStoredToken } from './api/client'
import './App.css'

export default function App() {
  const [token, setToken] = useState<string | null>(null)
  const [username, setUsername] = useState('')

  useEffect(() => {
    const stored = loadStoredToken()
    if (stored) {
      setAuthToken(stored)
      setToken(stored)
      setUsername(localStorage.getItem('auth_username') || '')
    }
  }, [])

  function handleAuth(t: string, u: string) {
    setToken(t)
    setUsername(u)
    localStorage.setItem('auth_username', u)
  }

  function handleLogout() {
    setAuthToken(null)
    setToken(null)
    setUsername('')
    localStorage.removeItem('auth_username')
  }

  if (!token) return <LoginPage onAuth={handleAuth} />
  return <DashboardPage username={username} onLogout={handleLogout} />
}
