import type { ApiErrorDetail, ApiErrorResponse } from './types'

export class ApiError extends Error {
  readonly status: number | null
  readonly code: string
  readonly requestId: string | null
  readonly details: ApiErrorDetail[]

  constructor(options: {
    message: string
    status?: number | null
    code?: string
    requestId?: string | null
    details?: ApiErrorDetail[]
  }) {
    super(options.message)
    this.name = 'ApiError'
    this.status = options.status ?? null
    this.code = options.code ?? 'NETWORK_ERROR'
    this.requestId = options.requestId ?? null
    this.details = options.details ?? []
  }
}

export function toApiError(
  response: Response,
  payload: unknown,
): ApiError {
  const body = payload as ApiErrorResponse | null
  const error = body && typeof body === 'object' && 'error' in body ? body.error : null

  return new ApiError({
    message: error?.message || `La requête a échoué (${response.status}).`,
    status: response.status,
    code: error?.code || 'HTTP_ERROR',
    requestId: response.headers.get('X-Request-ID') || error?.request_id || null,
    details: error?.details || [],
  })
}
