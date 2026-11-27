import { apiClient, setAccountToken } from './client'
import { ApiError } from './api-error'

export type AccountRole = 'candidate' | 'interviewer' | 'admin'

export interface Account {
  id: number
  email: string
  full_name: string
  role: AccountRole
  institution_id: number | null
  is_active: boolean
}

export interface AuthResult {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: Account
}

let restorePromise: Promise<Account> | null = null

function acceptSession(data: AuthResult): Account {
  if (!['candidate', 'interviewer', 'admin'].includes(data.user.role)) {
    setAccountToken(null)
    throw new ApiError({ code: 'UNSUPPORTED_ACCOUNT_ROLE', message: 'Votre accès doit être revu par un administrateur.' })
  }
  setAccountToken(data.access_token)
  return data.user
}

export async function login(email: string, password: string) {
  const { data } = await apiClient.post<AuthResult>('/api/v1/auth/login', { email, password })
  return acceptSession(data)
}

export async function register(email: string, full_name: string, password: string) {
  const { data } = await apiClient.post<AuthResult>('/api/v1/auth/register', { email, full_name, password })
  return acceptSession(data)
}

export async function restoreSession() {
  if (!restorePromise) {
    restorePromise = apiClient.post<AuthResult>('/api/v1/auth/refresh').then(({ data }) => {
      return acceptSession(data)
    }).finally(() => { restorePromise = null })
  }
  return restorePromise
}

export async function logout() {
  try {
    await apiClient.postAuthenticated<void>('/api/v1/auth/logout')
  } catch (error) {
    if (!(error instanceof ApiError && error.status === 401)) throw error
  }
  setAccountToken(null)
}

export async function activate(invitation_token: string, password: string) {
  await apiClient.post<void>('/api/v1/auth/activate', { invitation_token, password })
}
