import { useEffect, useState } from 'react'
import { getNews, safeHref } from '../api.js'
import { SCAM_TYPES } from '../constants.js'
import DemoBadge from '../components/DemoBadge.jsx'

const fmt = (iso) => {
  const d = iso ? new Date(iso) : null
  return d && !Number.isNaN(d.getTime()) ? d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : ''
}

export default function News() {
  const [res, setRes] = useState(null)
  const [type, setType] = useState('all')
  useEffect(() => { getNews().then(setRes) }, [])

  if (!res) return <p className="skeleton">Loading…</p>
  if (!res.ok) return <p className="error" role="alert">{res.message}</p>
  const items = Array.isArray(res.data) ? res.data : []
  const types = [...new Set(items.map((i) => i.scam_type).filter(Boolean))]
  const shown = type === 'all' ? items : items.filter((i) => i.scam_type === type)
  // Items marked demo by the API, or the whole list when it came from the demo file, are hand-prepared from real articles.
  const handPrepared = res.demo || items.some((i) => i.demo)

  return (
    <>
      <h1>Scam news</h1>
      <p className="muted">Each item links to the original report.</p>
      {handPrepared && <DemoBadge>Hand-picked from real articles. Live feeds were not available.</DemoBadge>}
      <div className="row" style={{ margin: '.75rem 0' }}>
        <label htmlFor="t" style={{ margin: 0 }}>Show</label>
        <select id="t" value={type} onChange={(e) => setType(e.target.value)}>
          <option value="all">All</option>
          {types.map((t) => <option key={t} value={t}>{SCAM_TYPES[t] ?? t}</option>)}
        </select>
      </div>
      {shown.length === 0 && <p className="muted">Nothing to show for this filter.</p>}
      {shown.map((n) => (
        <article key={n.url} className="card news-item">
          <h2>{safeHref(n.url) ? <a href={safeHref(n.url)} target="_blank" rel="noopener noreferrer">{n.title}</a> : n.title}</h2>
          <p className="muted">{[fmt(n.published_at), n.region, SCAM_TYPES[n.scam_type]].filter(Boolean).join(' · ')}</p>
          {n.summary && <p>{n.summary}</p>}
        </article>
      ))}
    </>
  )
}
