import { API_BASE_URL, apiClient } from './client'
import { toApiError } from './api-error'

type GuestSession = { id: string; access_token: string; refresh_token: string; expires_at: string }
export type ChatMessage = { id: string; role: string; content: string; language: string | null; created_at: string }
export type ChatConversation = { id: string; visitor_session_id: string; status: string; created_at: string; messages: ChatMessage[] }
type StoredGuest = { id: string; refresh_token: string; conversation_id?: string }
const KEY = 'smartcampus_guest_session'
let accessToken: string | null = null
let guestRefreshPromise: Promise<string> | null = null

export function pendingGuest(): StoredGuest | null {
  try { return JSON.parse(sessionStorage.getItem(KEY) || 'null') as StoredGuest | null } catch { return null }
}

function saveGuest(value: StoredGuest) { sessionStorage.setItem(KEY, JSON.stringify(value)) }
export function clearGuest() { sessionStorage.removeItem(KEY); accessToken = null }

async function guestRequest<T>(path: string, method: 'GET' | 'POST', body?: unknown): Promise<T> {
  const send = (token: string) => fetch(`${API_BASE_URL}${path}`, {
    method, credentials: 'include',
    headers: { Accept: 'application/json', Authorization: `Bearer ${token}`, ...(body === undefined ? {} : { 'Content-Type': 'application/json' }) },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  let response = await send(await guestAccessToken())
  if (response.status === 401) response = await send(await refreshGuest())
  const payload = await response.json().catch(() => null)
  if (!response.ok) throw toApiError(response, payload)
  return payload as T
}

export async function guestAccessToken(): Promise<string> {
  if (accessToken) return accessToken
  return refreshGuest()
}

export async function validateGuestSession(): Promise<void> {
  await refreshGuest()
}

async function refreshGuest(): Promise<string> {
  if (guestRefreshPromise) return guestRefreshPromise
  const saved = pendingGuest()
  if (!saved) throw new Error('No guest session')
  guestRefreshPromise = apiClient.post<GuestSession>(`/api/v1/visitor-sessions/${saved.id}/refresh`, { refresh_token: saved.refresh_token }).then(({ data }) => {
    saveGuest({ ...saved, refresh_token: data.refresh_token })
    accessToken = data.access_token
    return data.access_token
  }).finally(() => { guestRefreshPromise = null })
  return guestRefreshPromise
}

export async function startGuestConversation(language: 'fr' | 'tn' | 'arabizi' = 'fr'): Promise<ChatConversation> {
  const { data } = await apiClient.post<GuestSession>('/api/v1/visitor-sessions', { language })
  accessToken = data.access_token
  saveGuest({ id: data.id, refresh_token: data.refresh_token })
  const conversation = await guestRequest<ChatConversation>('/api/v1/conversations', 'POST', { channel: 'text', language })
  saveGuest({ ...(pendingGuest() || { id: data.id, refresh_token: data.refresh_token }), conversation_id: conversation.id })
  return conversation
}

export async function currentGuestConversation() {
  const saved = pendingGuest()
  if (!saved?.conversation_id) return null
  return guestRequest<ChatConversation>(`/api/v1/conversations/${saved.conversation_id}`, 'GET')
}

export async function sendGuestMessage(conversationId: string, content: string) {
  return guestRequest<ChatMessage>(`/api/v1/conversations/${conversationId}/messages`, 'POST', { content, content_type: 'text' })
}

export async function linkGuestSession() {
  const saved = pendingGuest()
  if (!saved) throw new Error('No guest session')
  const visitorToken = await refreshGuest()
  const { data } = await apiClient.postAuthenticatedWithHeaders<{ conversation_count: number }>(
    `/api/v1/visitor-sessions/${saved.id}/link`, { consent: true }, { 'X-Visitor-Session-Token': visitorToken },
  )
  clearGuest()
  return data
}
