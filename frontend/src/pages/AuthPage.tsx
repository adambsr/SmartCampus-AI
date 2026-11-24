import { useState, type FormEvent } from 'react'
import { ArrowRight, GraduationCap, LockKeyhole } from 'lucide-react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router'
import { useAuth } from '../components/shared/AuthContext'
import { activate } from '../services/api/auth'
import { ApiError } from '../services/api/api-error'
import './auth.css'

type Mode = 'login' | 'register' | 'activate'

function errorText(error: unknown) {
  return error instanceof ApiError ? error.message : 'Une erreur inattendue est survenue.'
}

export default function AuthPage({ mode }: { mode: Mode }) {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const { account, loading, signIn, signUp } = useAuth()
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [invitation, setInvitation] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [activated, setActivated] = useState(false)

  if (loading) return <div className="auth-loading">Vérification de la session…</div>
  if (account && mode !== 'activate') return <Navigate to={account.role === 'candidate' ? '/candidate' : '/staff'} replace />

  const next = params.get('next') === '/staff' ? '/staff' : '/candidate'
  const title = mode === 'register' ? 'Créer un compte candidat' : mode === 'activate' ? 'Activer votre compte' : 'Se connecter'

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      if (mode === 'activate') {
        await activate(invitation.trim(), password)
        setActivated(true)
        setPassword('')
        return
      }
      const user = mode === 'register'
        ? await signUp(email, fullName, password)
        : await signIn(email, password)
      navigate(user.role === 'candidate' ? (next === '/staff' ? '/candidate' : next) : '/staff', { replace: true })
    } catch (caught) {
      setError(errorText(caught))
    } finally {
      setBusy(false)
    }
  }

  return <main className="auth-page">
    <div className="auth-shell">
      <Link to="/" className="auth-brand"><span><GraduationCap size={22} /></span> SmartCampus AI</Link>
      <section className="auth-card" aria-labelledby="auth-title">
        <div className="auth-icon"><LockKeyhole size={24} /></div>
        <h1 id="auth-title">{title}</h1>
        <p>{mode === 'register' ? 'Créez votre espace pour consulter votre profil et vos candidatures.' : mode === 'activate' ? 'Saisissez le code d’invitation transmis par un administrateur et choisissez un mot de passe.' : 'Accédez à votre espace SmartCampus AI.'}</p>
        {activated ? <div className="auth-success" role="status">Compte activé. <Link to="/login">Vous pouvez maintenant vous connecter.</Link></div> :
          <form onSubmit={submit}>
            {mode === 'activate' ? <label>Code d’invitation<input autoComplete="off" required value={invitation} onChange={(event) => setInvitation(event.target.value)} /></label> :
              <label>Adresse e-mail<input type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></label>}
            {mode === 'register' && <label>Nom complet<input autoComplete="name" required maxLength={200} value={fullName} onChange={(event) => setFullName(event.target.value)} /></label>}
            <label>Mot de passe<input type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} required minLength={mode === 'login' ? undefined : 12} maxLength={mode === 'login' ? undefined : 128} value={password} onChange={(event) => setPassword(event.target.value)} /></label>
            {mode !== 'login' && <small>12 caractères minimum. Vous pouvez utiliser une phrase de passe.</small>}
            {error && <p className="auth-error" role="alert">{error}</p>}
            <button type="submit" className="auth-submit" disabled={busy}>{busy ? 'Veuillez patienter…' : mode === 'register' ? 'Créer mon compte' : mode === 'activate' ? 'Activer mon compte' : 'Se connecter'} <ArrowRight size={17} /></button>
          </form>}
        <div className="auth-links">
          {mode === 'login' && <><Link to="/register">Créer un compte candidat</Link><Link to="/activate">Activer un compte invité</Link></>}
          {mode !== 'login' && <Link to="/login">Déjà un compte ? Se connecter</Link>}
          <Link to="/">Retour à l’accueil</Link>
        </div>
      </section>
    </div>
  </main>
}
