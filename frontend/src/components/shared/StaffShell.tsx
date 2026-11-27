import { useState } from 'react'
import { BookOpen, GraduationCap, LogOut, Menu, Search, Users, X } from 'lucide-react'
import { Link, NavLink, useNavigate } from 'react-router'
import { useAuth } from './AuthContext'
import { staffRoleName } from './staff-role'

export function StaffShell({ children }: Readonly<{ children: React.ReactNode }>) {
  const { account, signOut } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [error, setError] = useState('')
  const canDossier = account?.role === 'academic_staff' || account?.role === 'interviewer'
  async function leave() { try { await signOut(); navigate('/', { replace: true }) } catch { setError('Déconnexion impossible. Réessayez.') } }
  return <div className="sc-staff"><aside className={`sc-staff-side ${open ? 'open' : ''}`}><Link className="sc-brand" to="/"><span className="sc-brand-mark"><GraduationCap size={23} /></span><span><strong>SmartCampus AI</strong><small>IIT · ISB SFAX</small></span></Link><p className="sc-side-caption">ESPACE DE TRAVAIL ACADÉMIQUE</p><div className="sc-side-role"><span>Rôle actif</span><strong>{staffRoleName(account?.role)}</strong></div><nav aria-label="Navigation staff"><NavLink to="/staff" end onClick={() => setOpen(false)}><BookOpen size={19} /> Vue d’ensemble</NavLink>{canDossier && <NavLink to="/staff/dossiers" onClick={() => setOpen(false)}><Search size={19} /> Dossiers candidats</NavLink>}<NavLink to="/catalog" onClick={() => setOpen(false)}><BookOpen size={19} /> Catalogue</NavLink>{account?.role === 'admin' && <NavLink to="/staff/users" onClick={() => setOpen(false)}><Users size={19} /> Gestion des comptes</NavLink>}</nav><button type="button" className="sc-side-logout" onClick={leave}><LogOut size={18} /> Déconnexion</button></aside>
    {open && <button type="button" className="sc-staff-scrim" aria-label="Fermer la navigation" onClick={() => setOpen(false)} />}
    <div className="sc-staff-main"><header className="sc-staff-top"><button type="button" className="sc-icon-button sc-staff-menu" aria-label={open ? 'Fermer le menu' : 'Ouvrir le menu'} onClick={() => setOpen(!open)}>{open ? <X /> : <Menu />}</button><strong>Espace de travail académique</strong><div><span>{account?.full_name}</span><small>{staffRoleName(account?.role)}</small></div><button type="button" className="sc-icon-button sc-staff-top-logout" onClick={leave} aria-label="Déconnexion"><LogOut size={18} /></button></header>{error && <p role="alert" className="sc-error">{error}</p>}<main className="sc-staff-content">{children}</main></div>
  </div>
}
