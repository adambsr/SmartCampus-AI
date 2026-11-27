import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router'
import { MessageSquareText, ShieldCheck, Save, Send } from 'lucide-react'
import { PublicShell } from '../components/shared/PublicShell'
import { ApiError } from '../services/api/api-error'
import { clearGuest, currentGuestConversation, pendingGuest, sendGuestMessage, startGuestConversation, type ChatConversation } from '../services/api/visitor'

type Language = 'fr' | 'tn' | 'arabizi'
export default function GuestChatPage() {
  const [conversation, setConversation] = useState<ChatConversation | null>(null)
  const [content, setContent] = useState('')
  const [language, setLanguage] = useState<Language>('fr')
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(Boolean(pendingGuest()?.conversation_id))
  const [error, setError] = useState('')
  useEffect(() => {
    let alive = true
    if (pendingGuest()?.conversation_id) currentGuestConversation().then((value) => { if (alive) setConversation(value) })
      .catch(() => { if (alive) { clearGuest(); setError('Votre session visiteur a expiré. Démarrez une nouvelle conversation.') } })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [])
  async function start() { setBusy(true); setError(''); try { setConversation(await startGuestConversation(language)) } catch (e) { setError(e instanceof ApiError ? e.message : 'Impossible de démarrer la conversation.') } finally { setBusy(false) } }
  async function send(event: FormEvent) { event.preventDefault(); if (!conversation || !content.trim()) return; setBusy(true); setError(''); try { const item = await sendGuestMessage(conversation.id, content.trim()); setConversation({ ...conversation, messages: [...conversation.messages, item] }); setContent('') } catch (e) { setError(e instanceof ApiError ? e.message : 'Impossible d’enregistrer le message.') } finally { setBusy(false) } }
  return <PublicShell><main className="sc-container sc-page sc-chat-page"><section className="sc-chat-workspace">
    <header className="sc-chat-heading"><div><p className="sc-eyebrow"><MessageSquareText size={19} /> Conversation visiteur</p><h1>Posez vos questions</h1><p>Vos messages texte sont enregistrés. Les réponses de l’assistant ne sont pas encore disponibles.</p></div><div className="sc-chat-session"><span>{conversation ? 'Session visiteur active' : 'Nouvelle session visiteur'}</span>{!conversation && <label>Langue des messages<select value={language} onChange={(e) => setLanguage(e.target.value as Language)}><option value="fr">Français</option><option value="tn">Tunisien</option><option value="arabizi">Arabizi</option></select></label>}</div></header>
    <div className="sc-chat-retain"><Save size={24} /><div><strong>Conserver vos échanges ?</strong><p>Créez un compte candidat ou connectez-vous pour associer cette session à votre espace, avec votre accord.</p></div><Link className="sc-button" to="/register">Créer un compte candidat</Link><Link className="sc-button secondary" to="/login">Se connecter</Link></div>
    <div className="sc-chat-info"><ShieldCheck size={18} /><span>Les messages sont conservés sur cette session. Aucune réponse automatique n’est générée.</span></div>
    <div className="sc-chat-body">{loading ? <div className="state-card" role="status">Restauration de la conversation…</div> : !conversation ? <div className="sc-chat-empty"><MessageSquareText size={34} /><h2>Votre conversation commence ici</h2><p>Choisissez la langue de vos messages, puis démarrez une session pour poser votre première question.</p><button className="sc-button" onClick={start} disabled={busy}>{busy ? 'Création…' : 'Démarrer une conversation'}</button></div> : <div className="sc-transcript" aria-live="polite">{conversation.messages.length ? conversation.messages.map((item) => <div key={item.id} className={`sc-message ${item.role === 'user' ? 'mine' : ''}`} dir="auto"><strong>{item.role === 'user' ? 'Vous' : 'Message'}</strong><p>{item.content}</p><small>{new Date(item.created_at).toLocaleString('fr-FR')}</small></div>) : <div className="sc-chat-empty"><MessageSquareText size={34} /><h2>Session prête</h2><p>Écrivez votre premier message ci-dessous.</p></div>}</div>}</div>
    {conversation && <form className="sc-chat-composer" onSubmit={send}><label htmlFor="guest-message">Votre message</label><textarea id="guest-message" value={content} onChange={(e) => setContent(e.target.value)} placeholder="Rédigez votre question ou votre message…" required /><div><span>{content.length} caractères</span><button className="sc-button" disabled={busy}><Send size={17} /> {busy ? 'Envoi…' : 'Envoyer le message'}</button></div></form>}
    {error && <p className="sc-error" role="alert">{error}</p>}
  </section></main></PublicShell>
}
