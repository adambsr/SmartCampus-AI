import { useState, type FormEvent } from 'react'
import { ArrowLeft, ArrowRight, Eye, EyeOff, GraduationCap, LockKeyhole, Mail, UserRound, UserRoundPlus, TicketCheck } from 'lucide-react'
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
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [invitation, setInvitation] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [activated, setActivated] = useState(false)

  if (loading) return <div className="auth-loading">Vérification de la session…</div>
  if (account && mode !== 'activate') return <Navigate to={account.role === 'candidate' ? '/candidate' : '/staff'} replace />

  const next = params.get('next') === '/staff' ? '/staff' : '/candidate'
  const title = mode === 'register' ? 'Créer un compte candidat' : mode === 'activate' ? 'Activation de compte sur invitation' : 'Connexion à votre espace'

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    if (mode !== 'login' && password !== confirmPassword) { setError('Les mots de passe ne correspondent pas.'); return }
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

  return <main className={`auth-page auth-${mode}`}>
    <header className="auth-topbar"><Link to="/" className="auth-brand"><span><GraduationCap size={22} /></span> SmartCampus <b>AI</b></Link></header>
    <div className="auth-shell">
      <Link to="/" className="auth-back"><ArrowLeft size={17} /> Retour à l’accueil</Link>
      <section className="auth-card" aria-labelledby="auth-title">
        <div className="auth-icon">{mode === 'activate' ? <TicketCheck size={27} /> : <GraduationCap size={27} />}</div>
        <h1 id="auth-title">{title}</h1>
        {mode === 'activate' && <p className="auth-description">Saisissez le code d’invitation transmis par un administrateur et choisissez un mot de passe.</p>}
        {activated ? <div className="auth-success" role="status">Compte activé. <Link to="/login">Vous pouvez maintenant vous connecter.</Link></div> :
          <form onSubmit={submit}>
            {mode === 'register' && <label>Nom complet<span className="auth-input"><UserRound size={17} /><input autoComplete="name" required maxLength={200} value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Prénom Nom" /></span></label>}
            {mode === 'activate' ? <label>Code d’invitation<span className="auth-input"><TicketCheck size={17} /><input autoComplete="off" required value={invitation} onChange={(event) => setInvitation(event.target.value)} /></span></label> :
              <label>Adresse e-mail universitaire ou personnelle<span className="auth-input"><Mail size={17} /><input type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="exemple@email.com" /></span></label>}
            <label>{mode === 'activate' ? 'Nouveau mot de passe' : 'Mot de passe'}<span className="auth-input"><LockKeyhole size={17} /><input type={showPassword ? 'text' : 'password'} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} required minLength={mode === 'login' ? undefined : 12} maxLength={mode === 'login' ? undefined : 128} value={password} onChange={(event) => setPassword(event.target.value)} /><button type="button" aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'} onClick={() => setShowPassword(!showPassword)}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></span></label>
            {mode !== 'login' && <><div className="auth-guidance"><strong>Exigences du mot de passe</strong><span>Au moins 12 caractères. Une phrase de passe est acceptée.</span></div><label>Confirmer le mot de passe<span className="auth-input"><LockKeyhole size={17} /><input type={showPassword ? 'text' : 'password'} autoComplete="new-password" required value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} /></span></label></>}
            {error && <p className="auth-error" role="alert">{error}</p>}
            <button type="submit" className="auth-submit" disabled={busy}>{busy ? 'Veuillez patienter…' : mode === 'register' ? 'Créer mon compte candidat' : mode === 'activate' ? 'Activer mon compte staff' : 'Se connecter à SmartCampus'} <ArrowRight size={17} /></button>
          </form>}
        <div className="auth-links">
          {mode === 'login' ? <><p className="auth-divider">AUTRES ACCÈS</p><Link to="/register"><UserRoundPlus size={19} /> Créer un compte candidat</Link><Link to="/activate"><TicketCheck size={19} /> Activer un compte sur invitation</Link></> : <Link to="/login"><UserRound size={18} /> Déjà un compte ? Se connecter</Link>}
        </div>
      </section>
    </div>
    <footer className="auth-footer">SmartCampus AI · IIT &amp; ISB Sfax</footer>
  </main>
}
