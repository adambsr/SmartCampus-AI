import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { StaffShell } from '../components/shared/StaffShell'
import { LoadState } from '../components/shared/LoadState'
import { staffApi, type CandidateDossier } from '../services/api/staff'
import { useAuth } from '../components/shared/AuthContext'
import { ApiError } from '../services/api/api-error'

export default function StaffDossierPage() {
  const { account } = useAuth()
  const { id } = useParams()
  const navigate = useNavigate()
  const validId = Boolean(id && Number.isSafeInteger(Number(id)) && Number(id) > 0)
  const [query, setQuery] = useState(id || '')
  const [dossier, setDossier] = useState<CandidateDossier | null>(null)
  const [loading, setLoading] = useState(validId)
  const [error, setError] = useState('')
  useEffect(() => {
    if (!id) return
    const number = Number(id)
    if (!Number.isSafeInteger(number) || number <= 0) return
    let alive = true
    staffApi.dossier(number).then(({ data }) => { if (alive) { setDossier(data); setError('') } }).catch((caught: unknown) => {
      if (!alive) return
      setDossier(null)
      setError(caught instanceof ApiError && caught.status === 403 ? 'Accès à ce dossier refusé.' : caught instanceof ApiError && caught.status === 404 ? 'Dossier introuvable.' : 'Impossible de charger le dossier.')
    }).finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [id])
  function search(event: FormEvent) { event.preventDefault(); if (!/^\d+$/.test(query) || Number(query) <= 0) { setError('Saisissez un identifiant numérique valide.'); return } setLoading(true); navigate(`/staff/dossiers/${Number(query)}`) }
  const fields = dossier ? [
    ['Nom', dossier.full_name], ['E-mail', dossier.email], ['Téléphone', dossier.phone],
    ['Année de naissance', dossier.birth_year?.toString()], ['Ville', dossier.city], ['Nationalité', dossier.nationality],
    ['Niveau actuel', dossier.current_level], ['Série du bac', dossier.bac_section],
    ['Année du bac', dossier.bac_year?.toString()], ['Moyenne du bac', dossier.bac_average],
    ['Dernier diplôme', dossier.last_diploma], ['Spécialité', dossier.last_diploma_specialty],
    ['Matières préférées', dossier.favorite_subjects?.join(', ')], ['Centres d’intérêt', dossier.interests?.join(', ')],
    ['Objectif', dossier.career_goal], ['Contraintes', dossier.constraints], ['Langue préférée', dossier.preferred_language],
  ] : []
  return <StaffShell><Link className="sc-back" to="/staff">← Retour à l’espace staff</Link><h1>Dossier candidat</h1><p>Consultation directe par identifiant numérique. {account?.role === 'admin' ? 'Vous pouvez consulter les profils des candidats IIT et ISB.' : 'Seuls les dossiers avec une candidature au statut entretien planifié sont accessibles.'}</p><form className="sc-search-row sc-panel" onSubmit={search}><label>Identifiant numérique du dossier<input inputMode="numeric" pattern="[0-9]+" value={query} onChange={(event) => setQuery(event.target.value)} required /></label><button className="sc-button">Consulter le dossier</button></form><LoadState loading={loading} error={error || (id && !validId ? 'Identifiant numérique invalide.' : '')}>{dossier?.id === Number(id) && <div className="sc-dossier"><div className="sc-panel sc-dossier-heading"><p className="sc-eyebrow">Dossier #{dossier.id} · Consultation en lecture seule</p><h2>{dossier.full_name}</h2></div><div className="sc-dossier-grid">{[['Identité et coordonnées', fields.slice(0, 6)], ['Parcours académique', fields.slice(6, 13)], ['Orientation et préférences', fields.slice(13)]].map(([title, group]) => <section className="sc-panel" key={title as string}><h2>{title as string}</h2><dl className="sc-facts">{(group as typeof fields).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value || 'Non renseigné'}</dd></div>)}</dl></section>)}</div></div>}</LoadState></StaffShell>
}
