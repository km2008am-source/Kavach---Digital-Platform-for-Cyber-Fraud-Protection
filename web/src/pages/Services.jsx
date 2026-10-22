import { useEffect, useState } from 'react'
import { getServices, safeHref } from '../api.js'
import { SITUATIONS } from '../constants.js'
import DemoBadge from '../components/DemoBadge.jsx'
import PageHeader from '../components/PageHeader.jsx'
import Icon from '../components/Icon.jsx'

const ICONS = { lost_money: 'phone', suspicious: 'message', lost_phone: 'app', id_misuse: 'user', investment: 'pulse', other: 'help' }

const domainOf = (url) => {
  try { return new URL(url).hostname.replace(/^www\./, '') } catch { return '' }
}

export default function Services() {
  const [res, setRes] = useState(null)
  useEffect(() => { getServices().then(setRes) }, [])

  const header = (
    <PageHeader icon="help" title="Get help">
      Official services only. Every card links to the government or regulator's own site.
    </PageHeader>
  )

  if (!res) return <>{header}<div className="wrap page-body"><p className="skeleton">Loading…</p></div></>
  if (!res.ok) return <>{header}<div className="wrap page-body"><p className="notice notice-error" role="alert"><Icon name="alert" />{res.message}</p></div></>

  const items = Array.isArray(res.data) ? res.data : []
  const known = new Set(SITUATIONS.map(([k]) => k))
  const groups = [...SITUATIONS, ...(items.some((i) => !known.has(i.situation)) ? [['other', 'Other']] : [])]
    .map(([key, title]) => [key, title, items.filter((i) => (key === 'other' ? !known.has(i.situation) : i.situation === key))])
    .filter(([, , rows]) => rows.length)

  const jump = (key) => document.getElementById(`svc-${key}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })

  return (
    <>
      {header}
      <div className="wrap page-body">
        {res.demo && <DemoBadge />}
        <h2 style={{ fontSize: '1.15rem' }}>What happened?</h2>
        <div className="jump">
          {groups.map(([key, title]) => (
            <a key={key} href={`#svc-${key}`} onClick={(e) => { e.preventDefault(); jump(key) }}>
              <Icon name={ICONS[key] ?? 'help'} size={18} />{title}
            </a>
          ))}
        </div>

        {groups.map(([key, title, rows]) => (
          <section key={key} id={`svc-${key}`} className="svc-group" aria-labelledby={`svc-h-${key}`}>
            <h2 id={`svc-h-${key}`}><Icon name={ICONS[key] ?? 'help'} />{title}</h2>
            <ul className="svc-list">
              {rows.map((s) => {
                const href = safeHref(s.link)
                return (
                  <li key={s.id} className="svc">
                    <div>
                      <h3>{s.name}</h3>
                      <p>{s.what}</p>
                      <p className="when"><strong>Use it when:</strong> {s.when}</p>
                    </div>
                    {href && (
                      <div>
                        <a className="btn btn-ghost" href={href} target="_blank" rel="noopener noreferrer">
                          <Icon name="external" size={18} />Official site
                        </a>
                        <span className="domain">{domainOf(href)}</span>
                      </div>
                    )}
                  </li>
                )
              })}
            </ul>
          </section>
        ))}
      </div>
    </>
  )
}
