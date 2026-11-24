import { useEffect, useState } from 'react'
import { ArrowLeft, GraduationCap, LogOut } from 'lucide-react'
import { Link, useNavigate } from 'react-router'
import { useAuth } from '../components/shared/AuthContext'
import { apiClient } from '../services/api/client'
import { ApiError } from '../services/api/api-error'
import './auth.css'

type CandidateProfile = {
  id: number
  full_name: string
  email: string
  current_level: string | null
  preferred_language: string
  interests: string[] | null
}
type Application = {
  id: number
  program_name: string
  institution_code: string
  status: string
}

export default function CandidateAccountPage() {
  const { account, signOut } = useAuth()
  const navigate = useNavigate()
  const [profile, setProfile] = useState<CandidateProfile | null>(null)
  const [applications, setApplications] = useState<Application[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(true)

  useEffect(() => {
    let alive = true
    Promise.all([
      apiClient.getAuthenticated<CandidateProfile>('/api/v1/candidates/me'),
      apiClient.getAuthenticated<{ items: Application[] }>('/api/v1/candidates/me/applications'),
    ]).then(([candidate, dossiers]) => {
      if (alive) { setProfile(candidate.data); setApplications(dossiers.data.items) }
    }).catch((caught: unknown) => {
      if (alive) setError(caught instanceof ApiError ? caught.message : 'Impossible de charger votre espace.')
    }).finally(() => { if (alive) setBusy(false) })
    return () => { alive = false }
  }, [])

  async function leave() {
    try {
      await signOut()
      navigate('/', { replace: true })
    } catch {
      setError('Déconnexion impossible pour le moment. Réessayez.')
    }
  }

  return <main className="account-page">
    <header className="account-topbar"><Link to="/" className="auth-brand"><span><GraduationCap size={21} /></span> SmartCampus AI</Link><button type="button" onClick={leave}><LogOut size={16} /> Déconnexion</button></header>
    <div className="account-content">
      <Link className="account-back" to="/"><ArrowLeft size={16} /> Accueil</Link>
      <h1>Mon espace candidat</h1>
      <p>Bienvenue, {account?.full_name}. Retrouvez les informations liées à votre compte.</p>
      {busy && <p role="status">Chargement de votre profil…</p>}
      {error && <p className="auth-error" role="alert">{error}</p>}
      {profile && <section className="account-panel"><h2>Mon profil</h2><dl><div><dt>Nom</dt><dd>{profile.full_name}</dd></div><div><dt>E-mail</dt><dd>{profile.email}</dd></div><div><dt>Niveau actuel</dt><dd>{profile.current_level || 'À compléter'}</dd></div><div><dt>Langue préférée</dt><dd>{profile.preferred_language}</dd></div><div><dt>Centres d’intérêt</dt><dd>{profile.interests?.join(', ') || 'À compléter'}</dd></div></dl></section>}
      {!busy && !error && <section className="account-panel"><h2>Mes candidatures</h2>{applications.length ? <ul className="application-list">{applications.map((item) => <li key={item.id}><strong>{item.program_name}</strong><span>{item.institution_code} · {item.status}</span></li>)}</ul> : <p>Aucune candidature enregistrée pour le moment.</p>}</section>}
    </div>
  </main>
}
