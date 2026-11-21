import { useState } from 'react'
import {
  ArrowDown, ArrowRight, Bot, BookOpen, Check, ChevronDown, Globe2, GraduationCap,
  Languages, Menu, MessageCircle, Send, Sparkles, X,
} from 'lucide-react'
import { Link } from 'react-router'
import iitLogo from '../../design-references/iit logo.png'
import isbLogo from '../../design-references/isb logo.png'
import campusBuilding from '../../design-references/iit isb building.webp'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { Card } from '../components/ui/card'

type Language = 'fr' | 'tn' | 'arabizi'

const languageNames: Record<Language, string> = {
  fr: 'Français',
  tn: 'عربي تونسي',
  arabizi: 'Arabizi',
}

const programs = [
  {
    school: 'IIT',
    name: 'Cycle Préparatoire Intégré',
    focus: 'Génie & technologie',
    description: 'Un parcours préparatoire aux études d’ingénierie et aux disciplines technologiques.',
    icon: BookOpen,
    tint: 'blue',
  },
  {
    school: 'IIT',
    name: 'Cycle Ingénieur',
    focus: 'Génie & technologie',
    description: 'Des formations en ingénierie, informatique, télécommunications et technologies appliquées.',
    icon: GraduationCap,
    tint: 'indigo',
  },
  {
    school: 'IIT',
    name: 'Licences spécialisées',
    focus: 'Informatique & sciences appliquées',
    description: 'Des parcours professionnalisants en sciences et technologies à Sfax.',
    icon: Sparkles,
    tint: 'teal',
  },
  {
    school: 'ISB',
    name: 'Programmes Business',
    focus: 'Management & sciences de gestion',
    description: 'Des parcours en gestion, finance, marketing digital et chaîne logistique.',
    icon: Globe2,
    tint: 'green',
  },
]

const steps = [
  {
    number: '01',
    title: 'Exprimez vos intérêts et votre parcours',
    text: 'Partagez votre niveau scolaire, vos matières préférées et vos objectifs.',
    icon: MessageCircle,
  },
  {
    number: '02',
    title: 'Comparez les filières IIT et ISB',
    text: 'Explorez les parcours et découvrez les éléments qui correspondent à votre profil.',
    icon: Sparkles,
  },
  {
    number: '03',
    title: 'Échangez dans votre langue',
    text: 'L’expérience est prévue en français, en arabe tunisien et en Arabizi.',
    icon: Languages,
  },
]

function Brand() {
  return (
    <Link to="/" className="brand" aria-label="SmartCampus AI, accueil">
      <span className="brand__mark"><GraduationCap size={21} strokeWidth={2.1} /></span>
      <span className="brand__text"><strong>SmartCampus <em>AI</em></strong><small>IIT · ISB SFAX</small></span>
    </Link>
  )
}

function CandidateLandingPage() {
  const [language, setLanguage] = useState<Language>('fr')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [notice, setNotice] = useState('')

  const showPreviewNotice = () => {
    setNotice('Cet espace sera accessible lorsque le service de candidature sera disponible.')
  }

  return (
    <div className="candidate-page">
      <div className="topline">
        <div className="site-container topline__inner">
          <span><GraduationCap size={14} /> Pôle Universitaire IIT &amp; ISB Sfax · Innovation académique</span>
          <span className="topline__location">Technopôle de Sfax, Route de Tunis Km 10</span>
        </div>
      </div>

      <header className="site-header">
        <div className="site-container site-header__inner">
          <Brand />
          <button
            type="button"
            className="mobile-menu-button"
            aria-label={mobileMenuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
            aria-expanded={mobileMenuOpen}
            onClick={() => setMobileMenuOpen((open) => !open)}
          >
            {mobileMenuOpen ? <X size={21} /> : <Menu size={21} />}
          </button>
          <nav className={`site-nav ${mobileMenuOpen ? 'site-nav--open' : ''}`} aria-label="Navigation principale">
            <a className="site-nav__active" href="#accueil" onClick={() => setMobileMenuOpen(false)}>Accueil</a>
            <a href="#programmes" onClick={() => setMobileMenuOpen(false)}>Programmes</a>
            <a href="#institutions" onClick={() => setMobileMenuOpen(false)}>À propos</a>
          </nav>
          <div className="site-header__actions">
            <label className="language-select" aria-label="Langue de la page">
              <Languages size={15} aria-hidden="true" />
              <select value={language} onChange={(event) => setLanguage(event.target.value as Language)}>
                {(Object.keys(languageNames) as Language[]).map((key) => <option key={key} value={key}>{languageNames[key]}</option>)}
              </select>
              <ChevronDown size={14} aria-hidden="true" />
            </label>
            <Button type="button" variant="secondary" size="small" onClick={showPreviewNotice}>
              Espace Candidat <ArrowRight size={15} />
            </Button>
          </div>
        </div>
      </header>

      <main>
        <section className="hero-section" id="accueil">
          <div className="site-container hero-grid">
            <div className="hero-copy">
              <Badge className="hero-tag"><span className="status-dot" /> Orientation &amp; admissions · IIT &amp; ISB Sfax</Badge>
              <h1>Trouvez votre voie universitaire à Sfax avec l’aide de l’intelligence artificielle.</h1>
              <p className="hero-copy__lead">Bacheliers et étudiants : explorez les cursus de l’IIT et de l’ISB, comparez les débouchés et découvrez les parcours d’orientation prévus par SmartCampus AI.</p>

              <div className="language-note">
                <span className="language-note__icon"><Languages size={18} /></span>
                <span><strong>Langues prévues pour les futurs échanges</strong><small>Français, Arabe Tunisien et Arabizi (Darija).</small></span>
                <div className="language-note__pills"><span>FR</span><span>عربي</span><span>ARZ</span></div>
              </div>

              <div className="hero-actions">
                <Button type="button" className="hero-primary" onClick={() => setNotice('Le service conversationnel n’est pas encore connecté. Vous pouvez déjà explorer les programmes ci-dessous.')}>
                  <Sparkles size={17} /> Démarrer une conversation
                </Button>
                <a className="text-link" href="#programmes">Explorer les programmes <ArrowRight size={16} /></a>
              </div>

              <div className="suggestions">
                <p>Questions fréquentes suggérées</p>
                <div className="suggestions__list">
                  <span><MessageCircle size={13} /> Quel cursus d’ingénieur choisir après mon bac ?</span>
                  <span><MessageCircle size={13} /> Différences entre licence IIT et ISB ?</span>
                  <span><MessageCircle size={13} /> Comment se passe l’orientation ?</span>
                </div>
              </div>
            </div>

            <div className="assistant-preview" aria-label="Aperçu illustratif de l’assistant, non connecté">
              <div className="assistant-preview__head">
                <span className="assistant-avatar"><Bot size={19} /></span>
                <div><strong>Conseiller SmartCampus</strong><small>IIT–ISB Sfax · Aperçu illustratif</small></div>
                <span className="assistant-preview__status"><span className="status-dot" /> Aperçu</span>
              </div>
              <div className="assistant-preview__body">
                <div className="chat-line chat-line--bot"><span className="chat-icon"><Bot size={14} /></span><p>Bonjour ! Je peux vous aider à découvrir les parcours de l’IIT et de l’ISB Sfax.<br /><br />Quelle filière vous intéresse ?</p></div>
                <div className="chat-line chat-line--user"><p>Je souhaite comparer les domaines de l’ingénierie et du management.</p></div>
                <div className="chat-line chat-line--bot"><span className="chat-icon"><Bot size={14} /></span><p>Vous pouvez commencer par explorer les programmes présentés ci-dessous. L’assistant conversationnel n’est pas encore connecté.</p></div>
                <div className="chat-topics"><span>Génie informatique</span><span>Business Analytics</span><span>Management</span></div>
              </div>
              <div className="assistant-preview__input"><span>Zone de conversation — aperçu uniquement</span><button type="button" disabled aria-label="Envoi indisponible"><Send size={15} /></button></div>
              <p className="assistant-preview__caption"><span className="status-dot" /> Langue sélectionnée : {languageNames[language]} · aperçu non connecté</p>
            </div>
          </div>
          <a className="scroll-cue" href="#programmes" aria-label="Découvrir les programmes"><ArrowDown size={16} /></a>
        </section>

        <section className="program-section" id="programmes">
          <div className="site-container">
            <div className="section-heading section-heading--split">
              <div>
                <p className="section-kicker"><span /> Parcours d’études disponibles</p>
                <h2>Des formations d’excellence à Sfax</h2>
                <p>Découvrez les parcours proposés au sein des institutions IIT et ISB.</p>
              </div>
              <div className="institution-chips"><Badge><GraduationCap size={13} /> IIT · Ingénierie</Badge><Badge><Globe2 size={13} /> ISB · Management</Badge></div>
            </div>
            <div className="program-grid">
              {programs.map((program) => {
                const Icon = program.icon
                return (
                  <Card key={program.name} className={`program-card program-card--${program.tint}`}>
                    <div className="program-card__top"><span className="program-card__icon"><Icon size={18} /></span><span className="program-school">{program.school}</span></div>
                    <h3>{program.name}</h3>
                    <p className="program-focus">{program.focus}</p>
                    <p className="program-description">{program.description}</p>
                    <a href="#institutions" className="program-link">Découvrir l’institution <ArrowRight size={14} /></a>
                  </Card>
                )
              })}
            </div>

            <div className="institution-banner" id="institutions">
              <img className="institution-banner__image" src={campusBuilding} alt="Bâtiment du pôle universitaire IIT et ISB à Sfax" />
              <div className="institution-banner__symbol"><GraduationCap size={30} /></div>
              <div className="institution-banner__copy">
                <span>Deux institutions · Un pôle universitaire</span>
                <h2>IIT &amp; ISB Sfax</h2>
                <p>Des parcours en ingénierie, technologies et sciences de gestion au sein du pôle universitaire de Sfax.</p>
              </div>
              <div className="institution-banner__schools"><span><strong>IIT</strong> Institut International de Technologie</span><span><strong>ISB</strong> International School of Business</span></div>
            </div>
          </div>
        </section>

        <section className="orientation-section" id="orientation">
          <div className="site-container">
            <div className="section-heading section-heading--center">
              <Badge className="section-label"><Sparkles size={13} /> Accompagnement d’orientation</Badge>
              <h2>Comment fonctionne l’assistant d’orientation ?</h2>
              <p>Un accompagnement pensé pour vous guider vers les formations IIT et ISB qui correspondent à votre profil.</p>
            </div>
            <div className="steps-grid">
              {steps.map((step) => {
                const Icon = step.icon
                return <Card className="step-card" key={step.number}><div className="step-card__top"><span>{step.number}</span><Icon size={18} /></div><h3>{step.title}</h3><p>{step.text}</p></Card>
              })}
            </div>
          </div>
        </section>

        <section className="institutions-section">
          <div className="site-container institutions-panel">
            <div className="institutions-panel__heading"><div><p className="section-kicker"><span /> Pôle universitaire privé</p><h2>L’alliance de deux institutions à Sfax</h2></div><div className="institutions-panel__notes"><span><Check size={14} /> Informations institutionnelles</span><span><Check size={14} /> Présentation des parcours</span></div></div>
            <div className="school-grid">
              <Card className="school-card"><img className="school-logo-image school-logo-image--iit" src={iitLogo} alt="Logo de l’Institut International de Technologie (IIT)" /><div><h3>Institut International de Technologie</h3><p>Pôle ingénierie &amp; sciences appliquées. Parcours en génie et technologies.</p><span><GraduationCap size={13} /> Technopôle de Sfax</span></div></Card>
              <Card className="school-card"><img className="school-logo-image school-logo-image--isb" src={isbLogo} alt="Logo de l’International School of Business (ISB)" /><div><h3>International School of Business</h3><p>Pôle management &amp; sciences de gestion. Parcours en business et management.</p><span><GraduationCap size={13} /> Sfax</span></div></Card>
            </div>
          </div>
        </section>

        <section className="closing-section">
          <div className="site-container closing-panel">
            <div><Badge className="closing-badge"><Sparkles size={13} /> Accompagnement d’orientation</Badge><h2>Prêt à définir votre futur académique ?</h2><p>Explorez les programmes de l’IIT et de l’ISB et préparez votre parcours.</p></div>
            <Button type="button" variant="secondary" onClick={() => setNotice('Le service conversationnel n’est pas encore connecté.')}><MessageCircle size={16} /> Découvrir l’assistant</Button>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="site-container">
          <div className="footer-grid"><div className="footer-brand"><Brand /><p>Plateforme universitaire dédiée à l’orientation entre les parcours de l’IIT et de l’ISB Sfax.</p></div><div><h3>IIT Sfax</h3><p>Génie &amp; technologie</p><p>Institut International de Technologie</p></div><div><h3>ISB Sfax</h3><p>Management &amp; sciences de gestion</p><p>International School of Business</p></div><div><h3>Informations</h3><p>Parcours universitaires</p><p>Assistance multilingue prévue</p></div></div>
          <div className="footer-bottom"><span>© SmartCampus AI · IIT &amp; ISB Sfax</span><Link to="/staff">Espace responsables</Link></div>
        </div>
      </footer>

      {notice && <div className="notice-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setNotice('') }}><section className="notice-dialog" role="dialog" tabIndex={-1} onKeyDown={(event) => { if (event.key === 'Escape') setNotice('') }} aria-modal="true" aria-labelledby="notice-title"><span className="notice-dialog__icon"><Bot size={21} /></span><h2 id="notice-title">Espace en préparation</h2><p>{notice}</p><Button type="button" autoFocus onClick={() => setNotice('')}>Compris</Button></section></div>}
    </div>
  )
}

export default CandidateLandingPage
