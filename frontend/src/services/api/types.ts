export interface ApiErrorDetail {
  field?: string | null
  reason?: string | null
}

export interface ApiErrorBody {
  code: string
  message: string
  details: ApiErrorDetail[]
  request_id: string | null
}

export interface ApiErrorResponse {
  error: ApiErrorBody
}

export interface ApiResponse<T> {
  data: T
  requestId: string | null
  status: number
}

export interface HealthResponse {
  status: string
  service: string
  timestamp: string
}
