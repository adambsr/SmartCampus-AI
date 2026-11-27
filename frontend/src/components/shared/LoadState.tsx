import type { ReactNode } from 'react'

export function LoadState({ loading, error, empty, children, retry }: Readonly<{ loading?: boolean; error?: string; empty?: string; children?: ReactNode; retry?: () => void }>) {
  if (loading) return <div className="state-card" role="status"><span className="state-skeleton" /><span className="state-skeleton short" /><span>Chargement…</span></div>
  if (error) return <div className="state-card state-error" role="alert"><p>{error}</p>{retry && <button type="button" className="sc-button secondary" onClick={retry}>Réessayer</button>}</div>
  if (empty) return <div className="state-card"><p>{empty}</p></div>
  return children
}
