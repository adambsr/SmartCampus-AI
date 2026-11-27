import { useEffect, useState, type FormEvent } from 'react'
import { ArrowRight, Search } from 'lucide-react'
import { Link, useSearchParams } from 'react-router'
import { PublicShell } from '../components/shared/PublicShell'
import { LoadState } from '../components/shared/LoadState'
import { catalogApi, type Institution, type ProgramList } from '../services/api/catalog'
import { programLevelName, teachingLanguageName } from '../components/shared/catalog-labels'

const PAGE_SIZE = 12
const levels = [['', 'Tous les niveaux'], ['prepa', 'Préparatoire'], ['licence', 'Licence'], ['ingenieur', 'Ingénieur'], ['mastere', 'Mastère'], ['mba', 'MBA'], ['architecture', 'Architecture']]
export default function CatalogPage() {
  const [params, setParams] = useSearchParams()
  const [draft, setDraft] = useState({ q: params.get('q') || '', institution: params.get('institution') || '', level: params.get('level') || '', field: params.get('field') || '', language: params.get('language') || '' })
  const [institutions, setInstitutions] = useState<Institution[]>([])
  const [result, setResult] = useState<ProgramList | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const page = Math.max(1, Number(params.get('page')) || 1)
  useEffect(() => { catalogApi.institutions().then(({ data }) => setInstitutions(Array.isArray(data) ? data : [])).catch(() => {}) }, [])
  useEffect(() => {
    const controller = new AbortController()
    const q = params.get('q') || ''
    catalogApi.list({ q: q.length >= 2 ? q : undefined, institution: params.get('institution') || undefined, level: params.get('level') || undefined, field: params.get('field') || undefined, language: params.get('language') || undefined, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE }, controller.signal)
      .then(({ data }) => setResult(data)).catch((caught: unknown) => { if (!controller.signal.aborted) setError(caught instanceof Error ? caught.message : 'Le catalogue est indisponible.') })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [params, page, attempt])
  function apply(event: FormEvent) {
    event.preventDefault()
    const next = new URLSearchParams()
    for (const [key, value] of Object.entries(draft)) if (value.trim()) next.set(key, value.trim())
    setLoading(true); setError(''); setParams(next)
  }
  const change = (key: keyof typeof draft, value: string) => setDraft((current) => ({ ...current, [key]: value }))
  const goPage = (nextPage: number) => { const next = new URLSearchParams(params); next.set('page', String(nextPage)); setLoading(true); setError(''); setParams(next); window.scrollTo({ top: 0 }) }
  return <PublicShell><main className="sc-container sc-page sc-catalog"><nav className="sc-breadcrumb" aria-label="Fil d’Ariane"><Link to="/">Accueil</Link><span>›</span><strong>Catalogue des formations</strong></nav><h1>Explorez les formations</h1><p className="sc-page-intro">Recherchez un programme et consultez ses informations publiées.</p>
    <form className="sc-filter-panel" onSubmit={apply}><div className="sc-filter-grid">
      <label>Rechercher une formation<input value={draft.q} onChange={(e) => change('q', e.target.value)} placeholder="Nom, code ou domaine" minLength={draft.q ? 2 : undefined} /></label>
      <label>Établissement<select value={draft.institution} onChange={(e) => change('institution', e.target.value)}><option value="">Tous les établissements</option>{institutions.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
      <label>Niveau<select value={draft.level} onChange={(e) => change('level', e.target.value)}>{levels.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label>Domaine<input value={draft.field} onChange={(e) => change('field', e.target.value)} placeholder="Ex. informatique" /></label>
      <label>Langue d’enseignement<select value={draft.language} onChange={(e) => change('language', e.target.value)}><option value="">Toutes les langues</option><option value="fr">Français</option><option value="en">Anglais</option></select></label>
    </div><div className="sc-actions"><button className="sc-button" type="submit"><Search size={17} /> Rechercher</button><button className="sc-button secondary" type="button" onClick={() => { setDraft({ q: '', institution: '', level: '', field: '', language: '' }); setLoading(true); setError(''); setParams(new URLSearchParams()) }}>Effacer les filtres</button></div></form>
    <div className="sc-results-heading"><h2>Résultats</h2>{result && !loading && <span>{result.total} formation{result.total > 1 ? 's' : ''}</span>}</div>
    <LoadState loading={loading} error={error} empty={!loading && !error && result?.items.length === 0 ? 'Aucune formation ne correspond à votre recherche.' : undefined} retry={() => { setLoading(true); setError(''); setAttempt((n) => n + 1) }}><div className="sc-results-grid">{result?.items.map((item) => <article className="sc-program-card" key={item.code}><div className="sc-card-tags"><span className={`sc-institution ${item.institution === 'ISB' ? 'isb' : ''}`}>{item.institution} Sfax</span><span className="sc-level">{programLevelName(item.level)}</span></div><h3>{item.name}</h3>{item.field && <p className="sc-card-field">{item.field}</p>}<div className="sc-card-spacer" /><p className="sc-card-language">Langue : {teachingLanguageName(item.teaching_language)}{item.duration_years ? ` · ${item.duration_years} ans` : ''}</p><Link to={`/programs/${encodeURIComponent(item.code)}`}>Voir le programme <ArrowRight size={19} /></Link></article>)}</div></LoadState>
    {!loading && !error && result && result.total > PAGE_SIZE && <nav className="sc-pagination" aria-label="Pagination"><button type="button" className="sc-button secondary" disabled={page <= 1} onClick={() => goPage(page - 1)}>Précédent</button><span>Page {page} sur {Math.ceil(result.total / PAGE_SIZE)}</span><button type="button" className="sc-button secondary" disabled={page * PAGE_SIZE >= result.total} onClick={() => goPage(page + 1)}>Suivant</button></nav>}
  </main></PublicShell>
}
