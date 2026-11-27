import { useEffect, useState } from 'react'
import { ArrowRight, BookOpen, GraduationCap, MessageCircle } from 'lucide-react'
import { Link } from 'react-router'
import { catalogApi, type ProgramSummary } from '../services/api/catalog'
import { PublicShell } from '../components/shared/PublicShell'
import campus from '../../design-references/iit isb building.webp'
import { LoadState } from '../components/shared/LoadState'
import { programLevelName, teachingLanguageName } from '../components/shared/catalog-labels'
import iitLogo from '../../design-references/iit logo.png'
import isbLogo from '../../design-references/isb logo.png'

export default function LandingPage() {
  const [programs, setPrograms] = useState<ProgramSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    catalogApi.list({ limit: 4, offset: 0 }, controller.signal).then(({ data }) => setPrograms(data.items))
      .catch((caught: unknown) => { if (!controller.signal.aborted) setError(caught instanceof Error ? caught.message : 'Le catalogue est indisponible.') })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [attempt])
  return <PublicShell>
    <main><section className="sc-hero"><div className="sc-container sc-hero-grid"><div>
      <p className="sc-eyebrow">Orientation &amp; formations · IIT &amp; ISB Sfax</p>
      <h1>Trouvez votre voie universitaire à Sfax.</h1>
      <p className="sc-lead">Explorez les formations de l’IIT et de l’ISB, leurs conditions d’admission et les informations publiées. Posez vos questions dans une conversation texte.</p>
      <div className="sc-actions"><Link className="sc-button" to="/chat"><MessageCircle size={18} /> Démarrer une conversation</Link><Link className="sc-button secondary" to="/catalog">Explorer le catalogue <ArrowRight size={18} /></Link></div>
      <p className="sc-hint">Les messages sont enregistrés. Les réponses de l’assistant ne sont pas encore disponibles.</p>
    </div><div className="sc-preview" aria-label="Présentation du service de conversation"><div className="sc-preview-top"><span className="sc-preview-icon"><GraduationCap size={24} /></span><div><strong>Un espace pour vos questions</strong><small>Conversation en français, tunisien ou Arabizi</small></div></div><div className="sc-preview-body"><BookOpen size={29} /><h2>Consultez les parcours et les règles d’admission</h2><p>Retrouvez les informations publiées par programme, puis conservez vos échanges si vous créez un compte candidat et acceptez leur transfert.</p><Link to="/chat">Ouvrir le chat <ArrowRight size={17} /></Link></div></div></div></section>
    <section className="sc-section"><div className="sc-container"><div className="sc-section-heading"><div><p className="sc-eyebrow">Catalogue académique</p><h2>Les formations disponibles</h2><p>Consultez les données du catalogue et ouvrez chaque fiche pour vérifier les détails publiés.</p></div><Link to="/catalog" className="sc-text-link">Toutes les formations <ArrowRight size={17} /></Link></div>
      <LoadState loading={loading} error={error} empty={!loading && !error && !programs.length ? 'Aucune formation publiée pour le moment.' : undefined} retry={() => { setError(''); setLoading(true); setAttempt((n) => n + 1) }}><div className="sc-program-grid">{programs.map((program) => <article className="sc-program-card" key={program.code}><div className="sc-program-icon"><GraduationCap size={23} /></div><p className="sc-program-meta">{program.institution} · {programLevelName(program.level)}</p><h3>{program.name}</h3><p>{[program.field, teachingLanguageName(program.teaching_language)].filter(Boolean).join(' · ')}</p><Link to={`/programs/${encodeURIComponent(program.code)}`}>Voir le programme <ArrowRight size={17} /></Link></article>)}</div></LoadState>
    </div></section><section className="sc-campus"><div className="sc-container sc-campus-grid"><div><p className="sc-eyebrow">IIT &amp; ISB Sfax</p><h2>Deux établissements, un même accès aux informations</h2><p>Découvrez les formations, les conditions d’admission et les campagnes disponibles depuis un catalogue commun.</p><div className="sc-logos"><img src={iitLogo} alt="Logo IIT" /><img src={isbLogo} alt="Logo ISB" /></div></div><img className="sc-campus-image" src={campus} alt="Campus IIT et ISB à Sfax" /></div></section>
    <section className="sc-how"><div className="sc-container"><div className="sc-how-intro"><p className="sc-eyebrow">Votre parcours d’orientation</p><h2>Comment utiliser SmartCampus AI ?</h2><p>Un accès simple aux informations publiées et à vos conversations.</p></div><div className="sc-how-grid"><article><span>01</span><BookOpen size={24} /><h3>Explorer les formations</h3><p>Consultez le catalogue, les fiches de programme et les règles d’admission publiées.</p></article><article><span>02</span><MessageCircle size={24} /><h3>Poser vos questions</h3><p>Enregistrez vos questions dans une conversation texte en français, tunisien ou Arabizi.</p></article><article><span>03</span><GraduationCap size={24} /><h3>Conserver vos échanges</h3><p>Créez un compte candidat, puis acceptez le transfert de votre session visiteur si vous le souhaitez.</p></article></div></div></section>
    <section className="sc-landing-final"><div className="sc-container"><div><p>SmartCampus AI · IIT &amp; ISB Sfax</p><h2>Prêt à explorer votre parcours ?</h2><span>Consultez les formations et gardez vos questions dans un espace de conversation.</span></div><Link className="sc-button secondary" to="/chat">Démarrer une conversation <ArrowRight size={17} /></Link></div></section></main>
  </PublicShell>
}
