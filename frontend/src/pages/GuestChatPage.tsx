import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router'
import { ApiError } from '../services/api/api-error'
import { clearGuest, currentGuestConversation, pendingGuest, sendGuestMessage, startGuestConversation, type ChatConversation } from '../services/api/visitor'
import './auth.css'

export default function GuestChatPage() {
  const [conversation, setConversation] = useState<ChatConversation | null>(null)
  const [content, setContent] = useState('')
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(Boolean(pendingGuest()?.conversation_id))
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    if (pendingGuest()?.conversation_id) currentGuestConversation().then((value) => {
      if (alive) setConversation(value)
    }).catch(() => { if (alive) { clearGuest(); setError('Votre session visiteur a expiré. Démarrez une nouvelle conversation.') } })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [])

  async function start() {
    setBusy(true); setError('')
    try { setConversation(await startGuestConversation()) }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : 'Impossible de démarrer la conversation.') }
    finally { setBusy(false) }
  }

  async function send(event: FormEvent) {
    event.preventDefault()
    if (!conversation || !content.trim()) return
    setBusy(true); setError('')
    try {
      const message = await sendGuestMessage(conversation.id, content.trim())
      setConversation({ ...conversation, messages: [...conversation.messages, message] })
      setContent('')
    } catch (caught) { setError(caught instanceof ApiError ? caught.message : 'Impossible d’enregistrer le message.') }
    finally { setBusy(false) }
  }

  return <main className="account-page"><header className="account-topbar"><Link to="/" className="auth-brand">SmartCampus AI</Link><Link to="/login">Se connecter</Link></header>
    <div className="account-content"><h1>Conversation visiteur</h1><p>Vos messages texte sont enregistrés. Les réponses de l’assistant ne sont pas encore disponibles.</p>
      {loading ? <p>Chargement…</p> : !conversation ? <button className="auth-submit" disabled={busy} onClick={start}>Démarrer une conversation</button> : <section className="account-panel">
        <div className="chat-transcript">{conversation.messages.length ? conversation.messages.map((message) => <p key={message.id}><strong>{message.role === 'user' ? 'Vous' : 'Assistant'} :</strong> {message.content}</p>) : <p>Aucun message pour le moment.</p>}</div>
        <form className="chat-form" onSubmit={send}><label htmlFor="guest-message">Votre message</label><textarea id="guest-message" value={content} onChange={(event) => setContent(event.target.value)} required /><button className="auth-submit" disabled={busy}>Envoyer</button></form>
      </section>}
      {error && <p className="auth-error" role="alert">{error}</p>}
      {conversation && <p className="chat-handoff">Vous souhaitez conserver toute cette session ? <Link to="/register">Créer un compte</Link> ou <Link to="/login">vous connecter</Link>, puis acceptez le transfert dans votre espace candidat.</p>}
    </div></main>
}
