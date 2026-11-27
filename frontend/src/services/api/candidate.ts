import { apiClient } from './client'
import type { ChatConversation } from './visitor'
import type { CandidateDossier } from './staff'

export type Application = { id: number; program_id: number; program_name: string; institution_code: string; status: string; consent_at: string | null; submitted_at: string | null }
export type ConversationSummary = { id: string; visitor_session_id: string; status: string; created_at: string }
export const candidateApi = {
  profile: (signal?: AbortSignal) => apiClient.getAuthenticated<CandidateDossier>('/api/v1/candidates/me', signal),
  applications: (signal?: AbortSignal) => apiClient.getAuthenticated<{ items: Application[] }>('/api/v1/candidates/me/applications', signal),
  conversations: (signal?: AbortSignal) => apiClient.getAuthenticated<{ items: ConversationSummary[] }>('/api/v1/candidates/me/conversations', signal),
  conversation: (id: string) => apiClient.getAuthenticated<ChatConversation>(`/api/v1/candidates/me/conversations/${encodeURIComponent(id)}`),
  send: (id: string, content: string) => apiClient.postAuthenticated<ChatConversation['messages'][number]>(`/api/v1/candidates/me/conversations/${encodeURIComponent(id)}/messages`, { content, content_type: 'text' }),
}
