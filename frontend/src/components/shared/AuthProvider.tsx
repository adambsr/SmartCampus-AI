import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { login, logout, register, restoreSession, type Account } from '../../services/api/auth'
import { AuthContext, type AuthContextValue } from './AuthContext'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [account, setAccount] = useState<Account | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let alive = true
    restoreSession().then((user) => {
      if (alive) setAccount(user)
    }).catch(() => {
      if (alive) setAccount(null)
    }).finally(() => {
      if (alive) setLoading(false)
    })
    return () => { alive = false }
  }, [])

  useEffect(() => {
    const lostSession = () => setAccount(null)
    window.addEventListener('smartcampus-auth-lost', lostSession)
    return () => window.removeEventListener('smartcampus-auth-lost', lostSession)
  }, [])

  const value = useMemo<AuthContextValue>(() => ({
    account,
    loading,
    signIn: async (email, password) => {
      const user = await login(email, password)
      setAccount(user)
      return user
    },
    signUp: async (email, fullName, password) => {
      const user = await register(email, fullName, password)
      setAccount(user)
      return user
    },
    signOut: async () => {
      await logout()
      setAccount(null)
    },
  }), [account, loading])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
