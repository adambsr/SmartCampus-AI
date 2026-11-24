import { useEffect, useState } from 'react'
import { ArrowLeft, GraduationCap, LogOut } from 'lucide-react'
import { Link, useNavigate } from 'react-router'
import { useAuth } from '../components/shared/AuthContext'
import { apiClient } from '../services/api/client'
import { ApiError } from '../services/api/api-error'
import { clearGuest, linkGuestSession, pendingGuest, validateGuestSession, type ChatConversation } from '../services/api/visitor'
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
type ConversationSummary = { id: string; visitor_session_id: string; status: string; created_at: string }

export default function CandidateAccountPage() {
  const { account, signOut } = useAuth()
  const navigate = useNavigate()
  const [profile, setProfile] = useState<CandidateProfile | null>(null)
  const [applications, setApplications] = useState<Application[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(true)
  const [guest, setGuest] = useState(pendingGuest())
  const [consent, setConsent] = useState(false)
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [selected, setSelected] = useState<ChatConversation | null>(null)
  const [message, setMessage] = useState('')
  const [transferring, setTransferring] = useState(false)

  useEffect(() => {
    let alive = true
    Promise.all([
      apiClient.getAuthenticated<CandidateProfile>('/api/v1/candidates/me'),
      apiClient.getAuthenticated<{ items: Application[] }>('/api/v1/candidates/me/applications'),
      apiClient.getAuthenticated<{ items: ConversationSummary[] }>('/api/v1/candidates/me/conversations'),
    ]).then(([candidate, dossiers, chats]) => {
      if (alive) { setProfile(candidate.data); setApplications(dossiers.data.items); setConversations(chats.data.items) }
    }).catch((caught: unknown) => {
      if (alive) setError(caught instanceof ApiError ? caught.message : 'Impossible de charger votre espace.')
    }).finally(() => { if (alive) setBusy(false) })
    return () => { alive = false }
  }, [])

  useEffect(() => {
    if (!guest?.conversation_id) return
    let alive = true
    validateGuestSession().catch((caught: unknown) => {
      if (alive && caught instanceof ApiError && [401, 404, 410].includes(caught.status ?? 0)) {
        clearGuest(); setGuest(null)
      }
    })
    return () => { alive = false }
  }, [guest?.conversation_id])

  async function leave() {
    try {
      await signOut()
      navigate('/', { replace: true })
    } catch {
      setError('Déconnexion impossible pour le moment. Réessayez.')
    }
  }

  async function transfer() {
    if (!guest || !consent) return
    setTransferring(true); setError('')
    try {
      await linkGuestSession()
      const { data } = await apiClient.getAuthenticated<{ items: ConversationSummary[] }>('/api/v1/candidates/me/conversations')
      setConversations(data.items); setGuest(null); setConsent(false)
    } catch (caught) {
      // A lost response may follow a committed transfer. Reconcile by account ownership.
      try {
        const { data } = await apiClient.getAuthenticated<{ items: ConversationSummary[] }>('/api/v1/candidates/me/conversations')
        if (data.items.some((item) => item.visitor_session_id === guest.id)) {
          clearGuest(); setGuest(null); setConversations(data.items); return
        }
      } catch { /* keep the original error */ }
      setError(caught instanceof ApiError ? caught.message : 'Le transfert a échoué. Réessayez.')
    } finally { setTransferring(false) }
  }

  async function openConversation(id: string) {
    try {
      const { data } = await apiClient.getAuthenticated<ChatConversation>(`/api/v1/candidates/me/conversations/${id}`)
      setSelected(data); setError('')
    } catch (caught) { setError(caught instanceof ApiError ? caught.message : 'Impossible de charger la conversation.') }
  }

  async function sendMessage(event: React.FormEvent) {
    event.preventDefault()
    if (!selected || !message.trim()) return
    try {
      const { data } = await apiClient.postAuthenticated<ChatConversation['messages'][number]>(
        `/api/v1/candidates/me/conversations/${selected.id}/messages`, { content: message.trim(), content_type: 'text' },
      )
      setSelected({ ...selected, messages: [...selected.messages, data] }); setMessage(''); setError('')
    } catch (caught) { setError(caught instanceof ApiError ? caught.message : 'Impossible d’enregistrer le message.') }
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
      {guest?.conversation_id && <section className="account-panel"><h2>Conserver votre conversation visiteur</h2><p>Si vous acceptez, toutes les conversations de cette session seront transférées définitivement à votre compte. L’accès visiteur prendra fin. Vous pourrez continuer ces conversations ici.</p><label className="consent-box"><input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} /> J’accepte le transfert de toute cette session.</label><button className="auth-submit" disabled={!consent || transferring} onClick={transfer}>{transferring ? 'Transfert…' : 'Associer à mon compte'}</button><button type="button" onClick={() => setGuest(null)}>Pas maintenant</button></section>}
      {!busy && <section className="account-panel"><h2>Mes conversations</h2>{conversations.length ? <ul className="application-list">{conversations.map((item) => <li key={item.id}><button type="button" onClick={() => openConversation(item.id)}>Conversation du {new Date(item.created_at).toLocaleString('fr-FR')}</button></li>)}</ul> : <p>Aucune conversation associée.</p>}{selected && <><h3>Historique</h3><div className="chat-transcript">{selected.messages.map((item) => <p key={item.id}><strong>{item.role === 'user' ? 'Vous' : 'Assistant'} :</strong> {item.content}</p>)}</div><form className="chat-form" onSubmit={sendMessage}><label htmlFor="candidate-message">Continuer la conversation</label><textarea id="candidate-message" value={message} onChange={(event) => setMessage(event.target.value)} required /><button className="auth-submit" disabled={selected.status !== 'active'}>Envoyer</button></form><p>Les réponses de l’assistant ne sont pas encore disponibles.</p></>}</section>}
      {!busy && !error && <section className="account-panel"><h2>Mes candidatures</h2>{applications.length ? <ul className="application-list">{applications.map((item) => <li key={item.id}><strong>{item.program_name}</strong><span>{item.institution_code} · {item.status}</span></li>)}</ul> : <p>Aucune candidature enregistrée pour le moment.</p>}</section>}
    </div>
  </main>
}
