import { useState, type FormEvent } from 'react'
import { ArrowRight, BookOpen, Search, Users } from 'lucide-react'
import { Link, useNavigate } from 'react-router'
import { StaffShell } from '../components/shared/StaffShell'
import { staffRoleName } from '../components/shared/staff-role'
import { useAuth } from '../components/shared/AuthContext'

export default function StaffDashboardPage() {
  const { account } = useAuth()
  const navigate = useNavigate()
  const [dossierId, setDossierId] = useState('')
  const canDossier = account?.role === 'academic_staff' || account?.role === 'interviewer'
  function lookup(event: FormEvent) { event.preventDefault(); if (/^[1-9]\d*$/.test(dossierId) && Number.isSafeInteger(Number(dossierId))) navigate(`/staff/dossiers/${dossierId}`) }
  return <StaffShell><div className="sc-staff-hero"><p className="sc-eyebrow">IIT &amp; ISB Sfax · {staffRoleName(account?.role)}</p><h1>Bonjour, {account?.full_name}</h1><p>Accédez aux fonctions disponibles pour votre rôle. Les dossiers restent soumis aux autorisations du backend.</p></div><div className="sc-staff-tiles">{canDossier && <section className="sc-panel sc-tile"><Search size={27} /><h2>Consulter un dossier</h2><p>Recherchez un candidat par identifiant numérique dans votre périmètre autorisé.</p><form className="sc-search-row" onSubmit={lookup}><label>Identifiant du dossier<input inputMode="numeric" pattern="[1-9][0-9]*" value={dossierId} onChange={(event) => setDossierId(event.target.value)} required /></label><button className="sc-button">Consulter</button></form></section>}<Link to="/catalog" className="sc-panel sc-tile"><BookOpen size={27} /><h2>Formations</h2><p>Consultez le catalogue public et ses informations publiées.</p><span>Voir le catalogue <ArrowRight size={17} /></span></Link>{account?.role === 'admin' && <Link to="/staff/users" className="sc-panel sc-tile"><Users size={27} /><h2>Gestion des comptes</h2><p>Créez des comptes staff en attente, gérez leurs accès et émettez des invitations.</p><span>Gérer les comptes <ArrowRight size={17} /></span></Link>}</div></StaffShell>
}
