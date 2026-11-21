import { useEffect, useState } from 'react'
import { Activity, CircleAlert, CircleCheck, LoaderCircle, RotateCw } from 'lucide-react'
import { Button } from '../ui/button'
import { ApiError } from '../../services/api/api-error'
import { API_BASE_URL } from '../../services/api/client'
import { checkApiHealth } from '../../services/api/health'

type HealthState =
  | { status: 'loading' }
  | { status: 'online'; service: string; timestamp: string; requestId: string | null }
  | { status: 'offline'; message: string; requestId: string | null }

export function HealthCheck() {
  const [health, setHealth] = useState<HealthState>({ status: 'loading' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    checkApiHealth(controller.signal).then((result) => {
      if (controller.signal.aborted) return
      setHealth({
        status: 'online',
        service: result.data.service,
        timestamp: result.data.timestamp,
        requestId: result.requestId,
      })
    }).catch((error: unknown) => {
      if (controller.signal.aborted) return
      const apiError = error instanceof ApiError ? error : null
      setHealth({
        status: 'offline',
        message: apiError?.message || 'Une erreur inattendue est survenue.',
        requestId: apiError?.requestId || null,
      })
    })
    return () => controller.abort()
  }, [attempt])

  return (
    <section className="health-check" aria-labelledby="health-title" aria-live="polite">
      <div className="health-check__heading">
        <span className="health-check__icon" aria-hidden="true"><Activity size={17} /></span>
        <div>
          <p className="eyebrow">Diagnostic technique</p>
          <h3 id="health-title">Connexion au serveur</h3>
        </div>
      </div>
      <p className="health-check__url">{API_BASE_URL}/api/v1/health</p>
      {health.status === 'loading' && (
        <p className="health-check__status"><LoaderCircle className="spin" size={16} /> Vérification en cours…</p>
      )}
      {health.status === 'online' && (
        <p className="health-check__status health-check__status--online">
          <CircleCheck size={16} /> API disponible · {health.service}
        </p>
      )}
      {health.status === 'offline' && (
        <div className="health-check__error">
          <p className="health-check__status health-check__status--offline">
            <CircleAlert size={16} /> API indisponible
          </p>
          <p>{health.message}</p>
          {health.requestId && <small>Référence : {health.requestId}</small>}
        </div>
      )}
      <Button
        type="button"
        variant="quiet"
        size="small"
        className="health-check__retry"
        onClick={() => {
          setHealth({ status: 'loading' })
          setAttempt((value) => value + 1)
        }}
        disabled={health.status === 'loading'}
      >
        <RotateCw size={14} /> Réessayer
      </Button>
    </section>
  )
}
