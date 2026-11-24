import { ApiError, toApiError } from './api-error'
import type { ApiResponse } from './types'

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()
export const API_BASE_URL = (configuredBaseUrl || '').replace(/\/+$/, '')
let accountToken: string | null = null
let refreshPromise: Promise<string> | null = null

export function setAccountToken(token: string | null) {
  accountToken = token
}

async function renewAccessToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = request<{ access_token: string }>('/api/v1/auth/refresh', {
      method: 'POST', auth: false,
    }).then(({ data }) => {
      accountToken = data.access_token
      return accountToken
    }).finally(() => { refreshPromise = null })
  }
  return refreshPromise
}

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH'
  body?: unknown
  signal?: AbortSignal
  auth?: boolean
  retry?: boolean
  headers?: Record<string, string>
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<ApiResponse<T>> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: options.method || 'GET',
      headers: {
        Accept: 'application/json',
        ...(options.body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...(options.auth && accountToken ? { Authorization: `Bearer ${accountToken}` } : {}),
        ...options.headers,
      },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      credentials: 'include',
      signal: options.signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError({
      message: 'Impossible de joindre le serveur. Vérifiez que le backend est démarré.',
      code: 'NETWORK_ERROR',
    })
  }

  if (response.status === 401 && options.auth && options.retry !== false) {
    try {
      await renewAccessToken()
      return request<T>(path, { ...options, retry: false })
    } catch {
      accountToken = null
      window.dispatchEvent(new Event('smartcampus-auth-lost'))
    }
  }
  const requestId = response.headers.get('X-Request-ID')
  let payload: unknown
  try {
    payload = await response.json()
  } catch {
    payload = null
  }

  if (!response.ok) throw toApiError(response, payload)
  return { data: payload as T, requestId, status: response.status }
}

export const apiClient = {
  get: <T>(path: string, signal?: AbortSignal) => request<T>(path, { signal }),
  getAuthenticated: <T>(path: string, signal?: AbortSignal) => request<T>(path, { signal, auth: true }),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body }),
  postAuthenticated: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body, auth: true }),
  postAuthenticatedWithHeaders: <T>(path: string, body: unknown, headers: Record<string, string>) => request<T>(path, { method: 'POST', body, auth: true, headers }),
  patchAuthenticated: <T>(path: string, body: unknown) => request<T>(path, { method: 'PATCH', body, auth: true }),
}
