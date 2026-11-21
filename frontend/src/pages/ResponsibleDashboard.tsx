import { useState } from 'react'
import {
  Activity, ArrowRight, Bell, BookOpen, Building2, CalendarCheck, ChartNoAxesColumn,
  ChevronDown, CircleHelp, ClipboardList, GraduationCap, LayoutDashboard, LockKeyhole,
  Menu, PanelLeftClose, Settings2, ShieldCheck, UserRound, Users, X,
} from 'lucide-react'
import { Link } from 'react-router'
import { HealthCheck } from '../components/shared/HealthCheck'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { Card } from '../components/ui/card'

const academicYear = import.meta.env.VITE_ACADEMIC_YEAR || '2026–2027'

const modules = [
  { title: 'Orientation & accompagnement IA', status: 'Périmètre prévu', description: 'Conception du moteur d’orientation scolaire et professionnelle adapté au contexte tunisien, avec prise en charge prévue du français, du derja et de l’arabizi.', icon: Activity, foot: 'Périmètre IIT · ISB' },
  { title: 'Suivi des candidatures', status: 'Spécification en cours', description: 'Module prévu pour la centralisation et la vérification des pièces de dossier selon les critères de chaque filière.', icon: ClipboardList, foot: 'Périmètre des cycles' },
  { title: 'Coordination des entretiens', status: 'Spécification en cours', description: 'Outils planifiés pour la préparation des entretiens et la consolidation des avis des commissions.', icon: CalendarCheck, foot: 'Périmètre des entretiens' },
  { title: 'Programmes & référentiels', status: 'Référentiel prévu', description: 'Présentation des filières d’ingénierie IIT et des parcours de gestion ISB pour l’orientation académique.', icon: BookOpen, foot: `Référentiel ${academicYear}` },
]

const roleLabels = ['Superviseur Académique IIT / ISB', 'Jury d’Entretien', 'Direction', 'Administration Système']

const navItems = [
  { label: 'Vue d’ensemble', icon: LayoutDashboard, href: '#overview' },
  { label: 'Candidats', icon: Users, href: '#modules' },
  { label: 'Orientation IA', icon: Activity, href: '#modules' },
  { label: 'Entretiens', icon: CalendarCheck, href: '#modules' },
  { label: 'Programmes', icon: BookOpen, href: '#modules' },
  { label: 'Rapports', icon: ChartNoAxesColumn, href: '#workspace' },
]

function ResponsibleDashboard() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [language, setLanguage] = useState('fr')
  const [notice, setNotice] = useState('')

  return (
    <div className="staff-layout">
      <aside className={`staff-sidebar ${menuOpen ? 'staff-sidebar--open' : ''}`}>
        <div className="staff-sidebar__brand"><Link to="/" className="staff-brand"><span><GraduationCap size={22} /></span><strong>SmartCampus AI<small>IIT &amp; ISB SFAX</small></strong></Link><Button type="button" variant="quiet" size="icon" className="sidebar-close" aria-label="Fermer le menu" onClick={() => setMenuOpen(false)}><X size={18} /></Button></div>
        <p className="staff-sidebar__context">Pôle IIT · ISB Sfax<br />Espace Responsables &amp; Staff</p>
        <nav className="staff-nav" aria-label="Navigation de l’espace responsables">
          {navItems.map(({ label, icon: Icon, href }, index) => <a className={index === 0 ? 'staff-nav__active' : ''} href={href} key={label} onClick={() => setMenuOpen(false)}><Icon size={18} /><span>{label}</span></a>)}
        </nav>
        <div className="staff-sidebar__bottom"><a href="#settings" onClick={(event) => { event.preventDefault(); setNotice('Les paramètres seront disponibles après attribution des rôles.') }}><Settings2 size={18} /> Paramètres</a><div className="staff-support"><div><CircleHelp size={16} /><strong>Assistance académique</strong></div><p>Assistance interne réservée aux équipes autorisées IIT &amp; ISB.</p><a href="#support" onClick={(event) => { event.preventDefault(); setNotice('Le guide interne sera disponible dans l’espace responsables.') }}>Guide d’assistance interne</a></div></div>
      </aside>

      <div className="staff-main">
        <header className="staff-topbar">
          <Button type="button" variant="quiet" size="icon" className="staff-menu-toggle" aria-label="Ouvrir la navigation" aria-expanded={menuOpen} onClick={() => setMenuOpen((open) => !open)}><Menu size={20} /></Button>
          <Link to="/" className="staff-mobile-brand" aria-label="SmartCampus AI, accueil"><span><GraduationCap size={17} /></span>SmartCampus AI</Link>
          <div className="staff-topbar__context"><Badge aria-label={`Session universitaire ${academicYear}`}><span className="session-dot" /> {academicYear}</Badge><span className="staff-location"><Building2 size={15} /> Technopôle &amp; Centre Sfax</span></div>
          <div className="staff-topbar__actions"><label className="language-select language-select--staff"><span className="sr-only">Langue</span><select value={language} onChange={(event) => setLanguage(event.target.value)}><option value="fr">Français</option><option value="tn">عربي تونسي</option><option value="arabizi">Arabizi</option></select><ChevronDown size={14} /></label><Button type="button" variant="quiet" size="icon" aria-label="Notifications, fonction non disponible" onClick={() => setNotice('Les notifications ne sont pas encore connectées.')}><Bell size={18} /></Button><div className="staff-profile"><span>Direction &amp; Équipe Académique<small>Pôle IIT · ISB Sfax</small></span><span className="staff-profile__avatar"><UserRound size={18} /></span></div></div>
        </header>

        <main className="staff-content" id="overview">
          <section className="staff-hero"><div className="staff-hero__copy"><Badge className="staff-hero__badge"><span className="status-dot" /> Portail officiel staff · IIT · ISB Sfax</Badge><h1>Bienvenue dans l’espace de gestion et d’orientation SmartCampus AI</h1><p>Ce pupitre centralisé présente les périmètres prévus pour le suivi de l’admission et l’orientation assistée par intelligence artificielle au sein de l’IIT et de l’ISB.</p></div><div className="staff-hero__meta"><span><span className="session-dot" /> Interface de démonstration</span><small>Session universitaire {academicYear}<br />Pôle IIT &amp; ISB Sfax</small></div><div className="staff-hero__facts"><span><Building2 size={15} /> IIT · Ingénierie &amp; technologies</span><span><Building2 size={15} /> ISB · Management &amp; business</span><span><GraduationCap size={15} /> Pôle universitaire de Sfax</span></div></section>

          <section className="modules-section" id="modules"><div className="modules-heading"><div><h2>Modules fonctionnels du pôle</h2><p>Périmètres de service prévus pour l’admission et l’orientation pédagogique.</p></div><Badge className="year-badge">Spécifications {academicYear}</Badge></div><div className="module-grid">{modules.map(({ title, status, description, icon: Icon, foot }) => <Card className="module-card" key={title}><div className="module-card__top"><span className="module-card__icon"><Icon size={20} /></span><Badge className="module-status">{status}</Badge></div><h3>{title}</h3><p>{description}</p><div className="module-card__footer"><span>{foot}</span><ArrowRight size={16} aria-hidden="true" /></div></Card>)}</div></section>

          <section className="workspace-card" id="workspace"><span className="workspace-icon"><ClipboardList size={31} /><span><LockKeyhole size={14} /></span></span><p className="workspace-eyebrow">Accès personnalisé par rôle</p><h2>Espace de travail en attente d’attribution de rôle</h2><p className="workspace-copy">L’espace sera personnalisé selon le rôle attribué. Les fonctionnalités, outils d’évaluation et prérogatives diffèrent selon le profil (superviseur académique IIT/ISB, membre du jury d’entretien, direction ou administrateur). Tous les rôles ne disposent pas des mêmes accès.</p><div className="role-list">{roleLabels.map((role) => <Badge key={role}>{role}</Badge>)}</div><div className="workspace-actions"><Button type="button" onClick={() => setNotice('Le guide staff sera disponible lorsque l’espace sera attribué.')}><BookOpen size={16} /> Consulter le guide staff</Button><Button type="button" variant="secondary" onClick={() => setNotice('Les coordonnées de la direction académique ne sont pas configurées dans cette version.')}><CircleHelp size={16} /> Contacter la direction académique</Button></div></section>

          <section className="compliance-grid" aria-label="Informations institutionnelles"><Card><ShieldCheck size={19} /><div><h3>Confidentialité &amp; conformité</h3><p>Les dossiers académiques doivent être traités selon les règles de protection des données étudiantes.</p></div></Card><Card><GraduationCap size={19} /><div><h3>Accréditations nationales</h3><p>Les diplômes sont homologués et reconnus par le Ministère de l’Enseignement Supérieur et de la Recherche Scientifique de Tunisie.</p></div></Card><Card><PanelLeftClose size={19} /><div><h3>Paramétrage des commissions</h3><p>Les périmètres de travail dépendent du rôle et des responsabilités attribués.</p></div></Card></section>

          <HealthCheck />
          <footer className="staff-footer"><span>SmartCampus AI · IIT &amp; ISB Sfax</span><span>Interface de présentation SA-8</span><Link to="/">Retour à l’accueil <ArrowRight size={13} /></Link></footer>
        </main>
      </div>
      {menuOpen && <button type="button" className="staff-scrim" aria-label="Fermer le menu" onClick={() => setMenuOpen(false)} />}
      {notice && <div className="notice-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setNotice('') }}><section className="notice-dialog" role="dialog" tabIndex={-1} onKeyDown={(event) => { if (event.key === 'Escape') setNotice('') }} aria-modal="true" aria-labelledby="staff-notice-title"><span className="notice-dialog__icon"><LockKeyhole size={20} /></span><h2 id="staff-notice-title">Fonctionnalité non disponible</h2><p>{notice}</p><Button type="button" autoFocus onClick={() => setNotice('')}>Compris</Button></section></div>}
    </div>
  )
}

export default ResponsibleDashboard
