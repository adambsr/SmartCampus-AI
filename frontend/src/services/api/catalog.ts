import { apiClient } from './client'

export type ProgramSummary = {
  code: string; name: string; institution: string; level: string
  program_type: string | null; field: string | null; duration_years: number | null
  teaching_language: string; labels: string[]; source_url: string | null
}
export type ProgramDetail = ProgramSummary & {
  institution_name: string; credits: number | null; start_month: number | null
  description: string | null; career_outcomes: string[]; key_modules: string[]
  specializations: { name: string; description: string | null }[]
  leads_to: { code: string; name: string; condition: string | null }[]
  reachable_from: { code: string; name: string; condition: string | null }[]
}
export type Institution = { code: string; name: string; city: string | null; website: string | null; program_count: number }
export type ProgramList = { total: number; items: ProgramSummary[] }
export type Campaign = { institution: string; academic_year: string; opens_at: string | null; closes_at: string | null; status: string }
export type Admission = {
  program_code: string; program_name: string; entry_level: string; selection_steps: string[]
  min_average: string | null; language_requirement: string | null; required_documents: string[]
  notes: string | null; source_url: string | null
  accepted_backgrounds: Record<'bac_section' | 'prepa_track' | 'licence_specialty' | 'diploma', string[]>
  campaign: Campaign | null
}
export type Eligibility = { program_code: string; kind: string; value: string; eligible: boolean | null; reason: string }
export type Tariff = { academic_year: string; student_category: string; amount: string; currency: string; period: string; installments: number | null; year_total_estimate: string | null; is_confirmed: boolean; notes: string | null; source_url: string | null }
export type ProgramTariffs = { program_code: string; program_name: string; published: boolean; tariffs: Tariff[]; fee_rules: { rule: string; percent: string | null; source_url: string | null }[]; message: string }
export type CatalogFilters = { q?: string; institution?: string; level?: string; field?: string; language?: string; limit?: number; offset?: number }

const query = (values: Record<string, string | number | undefined>) => {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(values)) if (value !== undefined && value !== '') params.set(key, String(value))
  return params.toString()
}
const codePath = (code: string) => `/api/v1/programs/${encodeURIComponent(code)}`

export const catalogApi = {
  institutions: (signal?: AbortSignal) => apiClient.get<Institution[]>('/api/v1/institutions', signal),
  list: (filters: CatalogFilters, signal?: AbortSignal) => apiClient.get<ProgramList>(`/api/v1/programs?${query(filters)}`, signal),
  detail: (code: string, signal?: AbortSignal) => apiClient.get<ProgramDetail>(codePath(code), signal),
  admission: (code: string, signal?: AbortSignal) => apiClient.get<Admission>(`${codePath(code)}/admission`, signal),
  tariffs: (code: string, signal?: AbortSignal) => apiClient.get<ProgramTariffs>(`${codePath(code)}/tariffs`, signal),
  campaigns: (institution?: string, signal?: AbortSignal) => apiClient.get<Campaign[]>(`/api/v1/campaigns?${query({ institution })}`, signal),
  eligibility: (code: string, kind: string, value: string) => apiClient.get<Eligibility>(`${codePath(code)}/eligibility?${query({ kind, value })}`),
}
