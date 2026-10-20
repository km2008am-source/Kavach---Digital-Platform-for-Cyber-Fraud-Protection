import { useEffect, useState } from 'react'
import { getServices, safeHref } from '../api.js'
import { SITUATIONS } from '../constants.js'
import DemoBadge from '../components/DemoBadge.jsx'

export default function Services() {
  const [res, setRes] = useState(null)
  useEffect(() => { getServices().then(setRes) }, [])

  if (!res) return <p className="skeleton">Loading…</p>
  if (!res.ok) return <p className="error" role="alert">{res.message}</p>
  const items = Array.isArray(res.data) ? res.data : []
  const known = new Set(SITUATIONS.map(([k]) => k))
  const groups = [...SITUATIONS, ...(items.some((i) => !known.has(i.situation)) ? [['other', 'Other']] : [])]

  return (
    <>
      <h1>Get help</h1>
      <p className="muted">Official services only. Every card links to the government or regulator's own site.</p>
      {res.demo && <DemoBadge />}
      {groups.map(([key, title]) => {
        const rows = items.filter((i) => (key === 'other' ? !known.has(i.situation) : i.situation === key))
        if (!rows.length) return null
        return (
          <section key={key} className="svc-group">
            <h2>{title}</h2>
            <div className="grid">
              {rows.map((s) => (
                <article key={s.id} className="card">
                  <h3 style={{ textTransform: 'none', color: 'inherit', fontSize: '1.1rem', margin: '0 0 .4rem' }}>{s.name}</h3>
                  <p>{s.what}</p>
                  <p className="muted"><strong>Use it when:</strong> {s.when}</p>
                  {safeHref(s.link) && <a href={safeHref(s.link)} target="_blank" rel="noopener noreferrer">Official site</a>}
                </article>
              ))}
            </div>
          </section>
        )
      })}
    </>
  )
}
