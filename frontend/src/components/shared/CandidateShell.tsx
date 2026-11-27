import { LogOut } from 'lucide-react'
import { Link, useNavigate } from 'react-router'
import { useState } from 'react'
import { useAuth } from './AuthContext'

export function CandidateShell({ children }: Readonly<{ children: React.ReactNode }>) {
  const { signOut } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  async function leave() { try { await signOut(); navigate('/', { replace: true }) } catch { setError('Déconnexion impossible. Réessayez.') } }
  return <div className="sc-candidate"><header className="sc-public-header"><div className="sc-container sc-header-inner"><Link to="/" className="sc-brand"><span className="sc-brand-mark">✣</span><span><strong>SmartCampus AI</strong><small>IIT · ISB SFAX</small></span></Link><nav aria-label="Navigation candidat"><Link to="/candidate">Mon espace</Link><Link to="/catalog">Formations</Link></nav><button className="sc-button secondary" onClick={leave}><LogOut size={17} /> Déconnexion</button></div></header>{error && <p role="alert" className="sc-error">{error}</p>}<main className="sc-container sc-page">{children}</main></div>
}
