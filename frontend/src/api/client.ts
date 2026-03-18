import axios from 'axios'
import type { AuthResponse, QueryResponse, HistoryItem } from '../types'

const api = axios.create({ baseURL: '/api' })

export function setAuthToken(token: string | null) {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Token ${token}`
    localStorage.setItem('auth_token', token)
  } else {
    delete api.defaults.headers.common['Authorization']
    localStorage.removeItem('auth_token')
  }
}

export function loadStoredToken(): string | null {
  return localStorage.getItem('auth_token')
}

export async function register(username: string, email: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/register', { username, email, password })
  return data
}

export async function login(username: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/login', { username, password })
  return data
}

export async function postQuery(question: string): Promise<QueryResponse> {
  const { data } = await api.post<QueryResponse>('/query', { question })
  return data
}

export async function getHistory(): Promise<HistoryItem[]> {
  const { data } = await api.get<{ results: HistoryItem[] }>('/history')
  return data.results
}
