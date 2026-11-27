import { apiClient } from './client'
import type { Account, AccountRole } from './auth'

export type StaffRole = Exclude<AccountRole, 'candidate'>
export type StaffCreate = { email: string; full_name: string; role: StaffRole; institution_id: number | null }
export type StaffUpdate = Partial<Pick<Account, 'institution_id' | 'is_active'>> & { role?: StaffRole }
export type Invitation = { invitation_token: string; expires_at: string }
export type CandidateDossier = {
  id: number; email: string; full_name: string; phone: string | null; birth_year: number | null
  city: string | null; nationality: string | null; current_level: string | null
  bac_section: string | null; bac_year: number | null; bac_average: string | null
  last_diploma: string | null; last_diploma_specialty: string | null
  favorite_subjects: string[] | null; interests: string[] | null
  career_goal: string | null; constraints: string | null; preferred_language: string
}
export const staffApi = {
  dossier: (id: number) => apiClient.getAuthenticated<CandidateDossier>(`/api/v1/candidates/${id}`),
  users: (limit: number, offset: number) => apiClient.getAuthenticated<{ items: Account[] }>(`/api/v1/admin/users?limit=${limit}&offset=${offset}`),
  create: (body: StaffCreate) => apiClient.postAuthenticated<Account>('/api/v1/admin/users', body),
  update: (id: number, body: StaffUpdate) => apiClient.patchAuthenticated<Account>(`/api/v1/admin/users/${id}`, body),
  invite: (id: number) => apiClient.postAuthenticated<Invitation>(`/api/v1/admin/users/${id}/invitations`),
}
