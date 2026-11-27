import { Link, NavLink } from 'react-router'
import { useAuth } from './AuthContext'

export function PublicShell({ children }: Readonly<{ children: React.ReactNode }>) {
  const { account } = useAuth()
  return <div className="sc-public"><header className="sc-public-header"><div className="sc-container sc-header-inner">
    <Link to="/" className="sc-brand"><span className="sc-brand-mark">✣</span><span><strong>SmartCampus AI</strong><small>IIT · ISB SFAX</small></span></Link>
    <nav aria-label="Navigation principale"><NavLink to="/" end>Accueil</NavLink><NavLink to="/catalog">Formations</NavLink><NavLink to="/chat">Chat visiteur</NavLink></nav>
    <Link className="sc-button" to={account ? account.role === 'candidate' ? '/candidate' : '/staff' : '/login'}>{account ? 'Mon espace' : 'Connexion'}</Link>
  </div></header>{children}<footer className="sc-public-footer"><div className="sc-container"><strong>SmartCampus AI · IIT &amp; ISB Sfax</strong><div><Link to="/catalog">Formations</Link><Link to="/chat">Chat visiteur</Link><Link to="/login">Connexion</Link></div></div></footer></div>
}

