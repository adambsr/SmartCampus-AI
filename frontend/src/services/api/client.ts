import { ApiError, toApiError } from './api-error'
import type { ApiResponse } from './types'

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()
export const API_BASE_URL = (configuredBaseUrl || 'http://127.0.0.1:8000').replace(/\/+$/, '')

async function request<T>(path: string, signal?: AbortSignal): Promise<ApiResponse<T>> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError({
      message: 'Impossible de joindre le serveur. Vérifiez que le backend est démarré.',
      code: 'NETWORK_ERROR',
    })
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

export const apiClient = { get: request }
