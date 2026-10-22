import { useEffect, useState } from 'react'
import { getNews, safeHref } from '../api.js'
import { SCAM_TYPES } from '../constants.js'
import DemoBadge from '../components/DemoBadge.jsx'
import PageHeader from '../components/PageHeader.jsx'
import Icon from '../components/Icon.jsx'

const fmt = (iso) => {
  const d = iso ? new Date(iso) : null
  return d && !Number.isNaN(d.getTime()) ? d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : ''
}

export default function News() {
  const [res, setRes] = useState(null)
  const [type, setType] = useState('all')
  useEffect(() => { getNews().then(setRes) }, [])

  const header = (
    <PageHeader icon="news" title="Scam news">Each item links to the original report.</PageHeader>
  )

  if (!res) return <>{header}<div className="wrap page-body"><p className="skeleton">Loading…</p></div></>
  if (!res.ok) return <>{header}<div className="wrap page-body"><p className="notice notice-error" role="alert"><Icon name="alert" />{res.message}</p></div></>

  const items = Array.isArray(res.data) ? res.data : []
  const types = [...new Set(items.map((i) => i.scam_type).filter(Boolean))]
  const shown = type === 'all' ? items : items.filter((i) => i.scam_type === type)
  // Items marked demo by the API, or the whole list when it came from the demo file, are hand-prepared from real articles.
  const handPrepared = res.demo || items.some((i) => i.demo)

  return (
    <>
      {header}
      <div className="wrap page-body">
        {handPrepared && <DemoBadge>Hand-picked from real articles. Live feeds were not available.</DemoBadge>}
        <div className="filters" role="group" aria-label="Show scam type">
          <button type="button" aria-pressed={type === 'all'} onClick={() => setType('all')}>All</button>
          {types.map((t) => (
            <button key={t} type="button" aria-pressed={type === t} onClick={() => setType(t)}>{SCAM_TYPES[t] ?? t}</button>
          ))}
        </div>

        {shown.length === 0 && <p className="muted">Nothing to show for this filter.</p>}
        <ul className="news-list">
          {shown.map((n) => {
            const href = safeHref(n.url)
            const date = fmt(n.published_at)
            return (
              <li key={n.url} className="news-item">
                <article>
                  <h2>{href ? <a href={href} target="_blank" rel="noopener noreferrer">{n.title}</a> : n.title}</h2>
                  <div className="news-meta">
                    {date && <time dateTime={n.published_at}>{date}</time>}
                    {n.region && <span className="tag tag-plain">{n.region}</span>}
                    {SCAM_TYPES[n.scam_type] && <span className="tag">{SCAM_TYPES[n.scam_type]}</span>}
                  </div>
                  {n.summary && <p>{n.summary}</p>}
                  {href && <a href={href} target="_blank" rel="noopener noreferrer" className="small">Read the original report<Icon name="external" size={15} /></a>}
                </article>
              </li>
            )
          })}
        </ul>
      </div>
    </>
  )
}
