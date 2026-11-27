import { useEffect, useState, type FormEvent } from 'react'
import { ArrowLeft, ExternalLink } from 'lucide-react'
import { Link, useParams } from 'react-router'
import { PublicShell } from '../components/shared/PublicShell'
import { LoadState } from '../components/shared/LoadState'
import { catalogApi, type Admission, type Campaign, type Eligibility, type ProgramDetail, type ProgramTariffs } from '../services/api/catalog'
import { ApiError } from '../services/api/api-error'
import { programLevelName, teachingLanguageName } from '../components/shared/catalog-labels'

type Part<T> = { value: T | null; loading: boolean; error: string }
const initial = <T,>(): Part<T> => ({ value: null, loading: true, error: '' })
const list = (items: string[]) => items.length ? <ul className="sc-detail-list">{items.map((item) => <li key={item}>{item}</li>)}</ul> : <p>Information non publiée.</p>
function Source({ url }: Readonly<{ url: string | null }>) {
  return url ? <a className="sc-source" href={url} target="_blank" rel="noopener noreferrer">Consulter la source <ExternalLink size={15} /></a> : null
}
export default function ProgramDetailPage() {
  const { code = '' } = useParams()
  const [program, setProgram] = useState<Part<ProgramDetail>>(initial)
  const [admission, setAdmission] = useState<Part<Admission>>(initial)
  const [tariffs, setTariffs] = useState<Part<ProgramTariffs>>(initial)
  const [campaigns, setCampaigns] = useState<Part<Campaign[]>>(initial)
  const [kind, setKind] = useState('bac_section')
  const [value, setValue] = useState('')
  const [eligibility, setEligibility] = useState<Eligibility | null>(null)
  const [eligibilityError, setEligibilityError] = useState('')
  const [eligibilityBusy, setEligibilityBusy] = useState(false)
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    if (!code) return
    const controller = new AbortController()
    catalogApi.detail(code, controller.signal).then(({ data }) => setProgram({ value: data, loading: false, error: '' })).catch((error: unknown) => { if (!controller.signal.aborted) setProgram({ value: null, loading: false, error: error instanceof ApiError && error.status === 404 ? 'Programme introuvable.' : 'Impossible de charger cette formation.' }) })
    catalogApi.admission(code, controller.signal).then(({ data }) => setAdmission({ value: data, loading: false, error: '' })).catch(() => { if (!controller.signal.aborted) setAdmission({ value: null, loading: false, error: 'Règles d’admission indisponibles.' }) })
    catalogApi.tariffs(code, controller.signal).then(({ data }) => setTariffs({ value: data, loading: false, error: '' })).catch(() => { if (!controller.signal.aborted) setTariffs({ value: null, loading: false, error: 'Tarifs indisponibles.' }) })
    return () => controller.abort()
  }, [code, attempt])
  const institution = program.value?.institution
  useEffect(() => {
    if (!institution) return
    const controller = new AbortController()
    catalogApi.campaigns(institution, controller.signal).then(({ data }) => setCampaigns({ value: data, loading: false, error: '' })).catch(() => { if (!controller.signal.aborted) setCampaigns({ value: null, loading: false, error: 'Campagnes indisponibles.' }) })
    return () => controller.abort()
  }, [institution])
  async function checkEligibility(event: FormEvent) {
    event.preventDefault()
    if (!value.trim()) return
    setEligibilityBusy(true); setEligibilityError(''); setEligibility(null)
    try { const { data } = await catalogApi.eligibility(code, effectiveKind, value.trim()); setEligibility(data) }
    catch (error) { setEligibilityError(error instanceof Error ? error.message : 'Vérification indisponible.') }
    finally { setEligibilityBusy(false) }
  }
  const availableKinds = admission.value?.accepted_backgrounds || { bac_section: [], prepa_track: [], licence_specialty: [], diploma: [] }
  const publishedKinds = Object.entries(availableKinds).filter(([, values]) => values.length)
  const effectiveKind = publishedKinds.some(([key]) => key === kind) ? kind : publishedKinds[0]?.[0] || kind
  const confirmedTariffs = tariffs.value?.published ? tariffs.value.tariffs.filter((item) => item.is_confirmed && item.source_url) : []
  return <PublicShell><main className="sc-container sc-page sc-detail"><Link className="sc-back" to="/catalog"><ArrowLeft size={17} /> Retour au catalogue</Link>
    <LoadState loading={program.loading} error={program.error} retry={() => { setProgram(initial()); setAdmission(initial()); setTariffs(initial()); setAttempt((n) => n + 1) }}>{program.value && <><p className="sc-eyebrow">{program.value.institution_name} · {programLevelName(program.value.level)}</p><h1>{program.value.name}</h1><p className="sc-page-intro">{program.value.description || 'Description non publiée.'}</p><div className="sc-fact-row"><span>Domaine : {program.value.field || 'Non indiqué'}</span><span>Langue : {teachingLanguageName(program.value.teaching_language)}</span>{program.value.duration_years && <span>Durée : {program.value.duration_years} ans</span>}{program.value.credits != null && <span>Crédits : {program.value.credits}</span>}</div><Source url={program.value.source_url} />
      <div className="sc-detail-grid"><div className="sc-detail-main"><section className="sc-panel"><h2>Parcours et débouchés</h2>{list(program.value.career_outcomes)}{program.value.key_modules.length > 0 && <><h3>Modules clés</h3>{list(program.value.key_modules)}</>}{program.value.specializations.length > 0 && <><h3>Spécialisations</h3>{list(program.value.specializations.map((item) => item.name))}</>}{program.value.leads_to.length > 0 && <><h3>Poursuite d’études</h3>{list(program.value.leads_to.map((item) => item.name))}</>}</section>
      <section className="sc-panel"><h2>Admission</h2><LoadState loading={admission.loading} error={admission.error}>{admission.value && <><p>Niveau d’entrée : {admission.value.entry_level}</p>{admission.value.min_average && <p>Moyenne minimale publiée : {admission.value.min_average}</p>}{admission.value.selection_steps.length > 0 && <><h3>Étapes de sélection</h3>{list(admission.value.selection_steps)}</>}{admission.value.language_requirement && <p>Langue requise : {admission.value.language_requirement}</p>}{admission.value.required_documents.length > 0 && <><h3>Documents requis</h3>{list(admission.value.required_documents)}</>}{admission.value.notes && <p>{admission.value.notes}</p>}<Source url={admission.value.source_url} /></>}</LoadState></section>
      <section className="sc-panel"><h2>Éligibilité indicative</h2>{publishedKinds.length ? <><p>Vérifiez si un parcours figure parmi les critères publiés. Ce résultat ne constitue pas une décision d’admission.</p><form className="sc-eligibility" onSubmit={checkEligibility}><label>Type de parcours<select value={effectiveKind} onChange={(event) => { setKind(event.target.value); setValue('') }}>{publishedKinds.map(([key]) => <option key={key} value={key}>{({ bac_section: 'Série du bac', prepa_track: 'Filière préparatoire', licence_specialty: 'Spécialité de licence', diploma: 'Diplôme' } as Record<string, string>)[key]}</option>)}</select></label><label>Votre parcours<select value={value} onChange={(event) => setValue(event.target.value)} required><option value="">Choisir</option>{(availableKinds[effectiveKind as keyof typeof availableKinds] || []).map((item) => <option key={item} value={item}>{item}</option>)}</select></label><button className="sc-button" disabled={eligibilityBusy}>Vérifier</button></form>{eligibility && <p role="status">{eligibility.reason}</p>}{eligibilityError && <p role="alert" className="sc-error">{eligibilityError}</p>}</> : <p>Critères d’éligibilité non publiés.</p>}</section></div>
      <aside className="sc-detail-aside"><section className="sc-panel"><h2>Campagne</h2><LoadState loading={campaigns.loading} error={campaigns.error}>{campaigns.value?.length ? campaigns.value.map((item) => <p key={item.academic_year}>{item.academic_year} · {item.status}{item.closes_at ? ` · Clôture : ${new Date(item.closes_at).toLocaleDateString('fr-FR')}` : ''}</p>) : <p>Statut de campagne non disponible.</p>}</LoadState></section><section className="sc-panel"><h2>Tarifs</h2><LoadState loading={tariffs.loading} error={tariffs.error}>{confirmedTariffs.length ? confirmedTariffs.map((item) => <div key={`${item.academic_year}-${item.student_category}`}><strong>{item.student_category} · {item.academic_year}</strong><p>{item.amount} {item.currency} / {item.period}</p><Source url={item.source_url} /></div>) : <p>Tarifs non confirmés. Consultez cette rubrique lorsque des montants publiés et sourcés seront disponibles.</p>}</LoadState></section></aside></div>
    </>}</LoadState>
  </main></PublicShell>
}
