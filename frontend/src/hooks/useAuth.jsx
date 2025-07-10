import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext()

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(localStorage.getItem('token'))

  // Base URL da API - ajustar conforme necessário
  const API_BASE_URL = 'http://localhost:5000/api'

  useEffect(() => {
    if (token) {
      // Verifica se o token é válido
      fetchCurrentUser()
    } else {
      setLoading(false)
    }
  }, [token])

  const fetchCurrentUser = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        setUser(data.user)
      } else {
        // Token inválido
        logout()
      }
    } catch (error) {
      console.error('Erro ao verificar usuário:', error)
      logout()
    } finally {
      setLoading(false)
    }
  }

  const login = async (email, password) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      })

      const data = await response.json()

      if (response.ok) {
        const { user, access_token } = data
        setUser(user)
        setToken(access_token)
        localStorage.setItem('token', access_token)
        return { success: true, user }
      } else {
        return { success: false, error: data.error || 'Erro no login' }
      }
    } catch (error) {
      console.error('Erro no login:', error)
      return { success: false, error: 'Erro de conexão' }
    }
  }

  const register = async (email, password, name, phone) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password, name, phone })
      })

      const data = await response.json()

      if (response.ok) {
        const { user, access_token } = data
        setUser(user)
        setToken(access_token)
        localStorage.setItem('token', access_token)
        return { success: true, user }
      } else {
        return { success: false, error: data.error || 'Erro no registro' }
      }
    } catch (error) {
      console.error('Erro no registro:', error)
      return { success: false, error: 'Erro de conexão' }
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('token')
  }

  const updateUser = (updatedUser) => {
    setUser(updatedUser)
  }

  // Função para fazer requisições autenticadas
  const apiRequest = async (endpoint, options = {}) => {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers
      },
      ...options
    }

    try {
      const response = await fetch(url, config)
      
      if (response.status === 401) {
        // Token expirado
        logout()
        throw new Error('Sessão expirada')
      }

      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.error || 'Erro na requisição')
      }

      return data
    } catch (error) {
      console.error('Erro na requisição:', error)
      throw error
    }
  }

  const value = {
    user,
    loading,
    token,
    login,
    register,
    logout,
    updateUser,
    apiRequest
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

