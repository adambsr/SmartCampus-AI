import { apiClient } from './client'
import type { HealthResponse } from './types'

export async function checkApiHealth(signal?: AbortSignal) {
  return apiClient.get<HealthResponse>('/api/v1/health', signal)
}
