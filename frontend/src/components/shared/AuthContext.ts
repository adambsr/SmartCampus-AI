import { createContext, useContext } from 'react'
import type { Account } from '../../services/api/auth'

export type AuthContextValue = {
  account: Account | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<Account>
  signUp: (email: string, fullName: string, password: string) => Promise<Account>
  signOut: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('AuthProvider is missing')
  return value
}
