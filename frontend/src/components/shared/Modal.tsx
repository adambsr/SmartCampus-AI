import { useEffect, useRef } from 'react'

export function Modal({ title, children, close }: Readonly<{ title: string; children: React.ReactNode; close: () => void }>) {
  const ref = useRef<HTMLDivElement>(null)
  const closeRef = useRef(close)
  useEffect(() => { closeRef.current = close }, [close])
  useEffect(() => {
    const prior = document.activeElement as HTMLElement | null
    ref.current?.querySelector<HTMLElement>('input, select, textarea, button')?.focus()
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') closeRef.current()
      if (event.key !== 'Tab' || !ref.current) return
      const items = [...ref.current.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), a[href]')]
      if (!items.length) return
      if (event.shiftKey && document.activeElement === items[0]) { event.preventDefault(); items.at(-1)?.focus() }
      else if (!event.shiftKey && document.activeElement === items.at(-1)) { event.preventDefault(); items[0].focus() }
    }
    document.addEventListener('keydown', onKey)
    return () => { document.removeEventListener('keydown', onKey); prior?.focus() }
  }, [])
  return <div className="sc-modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) close() }}><div className="sc-modal" ref={ref} role="dialog" aria-modal="true" aria-labelledby="sc-modal-title"><div className="sc-modal-head"><h2 id="sc-modal-title">{title}</h2><button type="button" className="sc-icon-button" aria-label="Fermer" onClick={close}>×</button></div>{children}</div></div>
}
