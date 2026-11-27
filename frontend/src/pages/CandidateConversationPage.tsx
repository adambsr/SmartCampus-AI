import { useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router'
import { CandidateShell } from '../components/shared/CandidateShell'
import { LoadState } from '../components/shared/LoadState'
import { candidateApi } from '../services/api/candidate'
import type { ChatConversation } from '../services/api/visitor'

export default function CandidateConversationPage() {
  const { id = '' } = useParams()
  const [conversation, setConversation] = useState<ChatConversation | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [sendError, setSendError] = useState('')
  const [attempt, setAttempt] = useState(0)
  useEffect(() => { let alive = true; candidateApi.conversation(id).then(({ data }) => { if (alive) setConversation(data) }).catch((e: unknown) => { if (alive) setError(e instanceof Error ? e.message : 'Conversation indisponible.') }).finally(() => { if (alive) setLoading(false) }); return () => { alive = false } }, [id, attempt])
  async function send(event: FormEvent) { event.preventDefault(); if (!conversation || !message.trim()) return; setSending(true); setSendError(''); try { const { data } = await candidateApi.send(id, message.trim()); setConversation({ ...conversation, messages: [...conversation.messages, data] }); setMessage('') } catch (e) { setSendError(e instanceof Error ? e.message : 'Envoi impossible.') } finally { setSending(false) } }
  return <CandidateShell><Link className="sc-back" to="/candidate">← Retour à mon espace</Link><h1>Historique de conversation</h1><p className="sc-page-intro">Vos messages texte enregistrés. Les réponses de l’assistant ne sont pas encore disponibles.</p><LoadState loading={loading} error={error} retry={() => { setLoading(true); setError(''); setAttempt((n) => n + 1) }}>{conversation && <section className="sc-panel sc-chat"><p>Créée le {new Date(conversation.created_at).toLocaleString('fr-FR')}</p><div className="sc-transcript" aria-live="polite">{conversation.messages.length ? conversation.messages.map((item) => <div key={item.id} className={`sc-message ${item.role === 'user' ? 'mine' : ''}`} dir="auto"><strong>{item.role === 'user' ? 'Vous' : 'Message'}</strong><p>{item.content}</p><small>{new Date(item.created_at).toLocaleString('fr-FR')}</small></div>) : <p>Aucun message enregistré.</p>}</div>{conversation.status === 'active' ? <form className="sc-form" onSubmit={send}><label htmlFor="candidate-message">Continuer la conversation<textarea id="candidate-message" value={message} onChange={(e) => setMessage(e.target.value)} required /></label>{sendError && <p className="sc-error" role="alert">{sendError}</p>}<button className="sc-button" disabled={sending}>{sending ? 'Envoi…' : 'Envoyer le message'}</button></form> : <p className="sc-hint">Cette conversation est fermée.</p>}</section>}</LoadState></CandidateShell>
}
