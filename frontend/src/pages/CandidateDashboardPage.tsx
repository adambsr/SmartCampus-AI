import { useEffect, useState } from 'react'
import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router'
import { CandidateShell } from '../components/shared/CandidateShell'
import { LoadState } from '../components/shared/LoadState'
import { Modal } from '../components/shared/Modal'
import { useAuth } from '../components/shared/AuthContext'
import { candidateApi, type Application, type ConversationSummary } from '../services/api/candidate'
import { clearGuest, linkGuestSession, pendingGuest, validateGuestSession } from '../services/api/visitor'
import type { CandidateDossier } from '../services/api/staff'

type Part<T> = { data: T | null; loading: boolean; error: string }
const pending = <T,>(): Part<T> => ({ data: null, loading: true, error: '' })
export default function CandidateDashboardPage() {
  const { account } = useAuth()
  const [profile, setProfile] = useState<Part<CandidateDossier>>(pending)
  const [applications, setApplications] = useState<Part<Application[]>>(pending)
  const [conversations, setConversations] = useState<Part<ConversationSummary[]>>(pending)
  const [guest, setGuest] = useState(pendingGuest())
  const [showConsent, setShowConsent] = useState(Boolean(pendingGuest()?.conversation_id))
  const [consent, setConsent] = useState(false)
  const [transferring, setTransferring] = useState(false)
  const [transferError, setTransferError] = useState('')
  const [transferNotice, setTransferNotice] = useState('')
  const [refresh, setRefresh] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    candidateApi.profile(controller.signal).then(({ data }) => setProfile({ data, loading: false, error: '' })).catch((e: unknown) => { if (!controller.signal.aborted) setProfile({ data: null, loading: false, error: e instanceof Error ? e.message : 'Profil indisponible.' }) })
    candidateApi.applications(controller.signal).then(({ data }) => setApplications({ data: data.items, loading: false, error: '' })).catch((e: unknown) => { if (!controller.signal.aborted) setApplications({ data: null, loading: false, error: e instanceof Error ? e.message : 'Candidatures indisponibles.' }) })
    candidateApi.conversations(controller.signal).then(({ data }) => setConversations({ data: data.items, loading: false, error: '' })).catch((e: unknown) => { if (!controller.signal.aborted) setConversations({ data: null, loading: false, error: e instanceof Error ? e.message : 'Conversations indisponibles.' }) })
    return () => controller.abort()
  }, [refresh])
  useEffect(() => {
    if (!guest?.conversation_id) return
    validateGuestSession().catch(() => { clearGuest(); setGuest(null); setShowConsent(false) })
  }, [guest?.conversation_id])
  async function transfer() {
    if (!guest || !consent) return
    setTransferring(true); setTransferError('')
    try {
      await linkGuestSession()
      setGuest(null); setShowConsent(false); setConsent(false)
      setTransferNotice('Vos conversations visiteur ont été transférées.')
      setRefresh((n) => n + 1)
    } catch (caught) {
      try {
        const { data } = await candidateApi.conversations()
        if (data.items.some((item) => item.visitor_session_id === guest.id)) {
          clearGuest(); setGuest(null); setShowConsent(false); setConversations({ data: data.items, loading: false, error: '' }); setTransferNotice('Vos conversations visiteur ont été transférées.'); return
        }
      } catch { /* retain the transfer error */ }
      setTransferError(caught instanceof Error ? caught.message : 'Transfert impossible.')
    } finally { setTransferring(false) }
  }
  return <CandidateShell><p className="sc-eyebrow">Espace candidat</p><h1>Bonjour, {account?.full_name}</h1><p className="sc-page-intro">Consultez votre profil, vos candidatures et les conversations associées à votre compte.</p>{transferNotice && <p className="sc-success" role="status">{transferNotice}</p>}
    <div className="sc-candidate-grid"><section className="sc-panel"><h2>Mon profil</h2><LoadState loading={profile.loading} error={profile.error} retry={() => setRefresh((n) => n + 1)}>{profile.data && <dl className="sc-facts"><div><dt>Nom</dt><dd>{profile.data.full_name}</dd></div><div><dt>E-mail</dt><dd>{profile.data.email}</dd></div><div><dt>Niveau actuel</dt><dd>{profile.data.current_level || 'Non renseigné'}</dd></div><div><dt>Langue préférée</dt><dd>{profile.data.preferred_language}</dd></div></dl>}</LoadState></section>
      <section className="sc-panel"><h2>Mes candidatures</h2><LoadState loading={applications.loading} error={applications.error} empty={applications.data?.length === 0 ? 'Aucune candidature enregistrée.' : undefined} retry={() => setRefresh((n) => n + 1)}><ul className="sc-simple-list">{applications.data?.map((item) => <li key={item.id}><strong>{item.program_name}</strong><span>{item.institution_code} · {item.status}</span></li>)}</ul></LoadState></section></div>
    <section className="sc-panel"><div className="sc-title-row"><h2>Mes conversations</h2>{guest?.conversation_id && <button className="sc-button secondary" onClick={() => setShowConsent(true)}>Conserver ma session visiteur</button>}</div><LoadState loading={conversations.loading} error={conversations.error} empty={conversations.data?.length === 0 ? 'Aucune conversation associée.' : undefined} retry={() => setRefresh((n) => n + 1)}><ul className="sc-simple-list">{conversations.data?.map((item) => <li key={item.id}><span>Conversation du {new Date(item.created_at).toLocaleString('fr-FR')}</span><Link to={`/candidate/conversations/${item.id}`}>Ouvrir <ArrowRight size={17} /></Link></li>)}</ul></LoadState></section>
    {showConsent && guest?.conversation_id && <Modal title="Conserver vos conversations" close={() => setShowConsent(false)}><p>Toutes les conversations de cette session visiteur seront liées à votre compte. L’accès visiteur à cette session prendra fin.</p><label className="sc-check"><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} /> J’accepte le transfert de toute cette session.</label>{transferError && <p className="sc-error" role="alert">{transferError}</p>}<div className="sc-actions"><button type="button" className="sc-button" disabled={!consent || transferring} onClick={transfer}>{transferring ? 'Transfert…' : 'Transférer'}</button><button type="button" className="sc-button secondary" onClick={() => setShowConsent(false)}>Pas maintenant</button></div></Modal>}
  </CandidateShell>
}
