import { useCallback, useEffect, useState } from 'react'
import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { pulseAlerts, pulseReplay } from '../api.js'
import { SCAM_TYPES, alertRadius, districtPos } from '../constants.js'
import DemoBadge from '../components/DemoBadge.jsx'
import PageHeader from '../components/PageHeader.jsx'
import Icon from '../components/Icon.jsx'

const POLL_MS = 5000
const COLOR = { confirmed: '#b3261e', emerging: '#d98a0b' }

export default function Pulse() {
  const [res, setRes] = useState(null)
  const [msg, setMsg] = useState('')
  const load = useCallback(() => pulseAlerts().then(setRes), [])

  useEffect(() => {
    load()
    const id = setInterval(load, POLL_MS)
    return () => clearInterval(id)
  }, [load])

  const replay = async () => {
    setMsg('')
    const r = await pulseReplay()
    if (!r.ok) setMsg(r.error === 'replay_disabled' ? 'Replay is switched off on this server (it needs DEMO_MODE=1).' : r.message)
    else { setMsg('Replay started. Watch the circle grow.'); load() }
  }

  const alerts = res?.ok && Array.isArray(res.data) ? res.data : []

  return (
    <>
      <PageHeader icon="pulse" title="Scam Pulse">
        Anonymous reports are grouped by wording to spot a scam wave early. <strong>This page runs on a seeded replay, not real national data.</strong>
      </PageHeader>

      <div className="wrap page-body">
        {res?.demo && <DemoBadge />}
        {res && !res.ok && <p className="notice notice-error" role="alert"><Icon name="alert" />{res.message}</p>}

        <div className="pulse-bar">
          <div className="btn-row">
            <button onClick={replay}><Icon name="replay" />Replay demo wave</button>
            {msg && <span role="status">{msg}</span>}
          </div>
          <div className="legend" aria-label="Map legend">
            <span><i className="dot dot-emerging" />Emerging wave</span>
            <span><i className="dot dot-confirmed" />Confirmed by news reports</span>
          </div>
        </div>

        <div className="pulse-grid">
          <div className="map">
            <MapContainer center={[10.9, 78.4]} zoom={7} style={{ height: '100%', width: '100%' }} scrollWheelZoom={false}>
              <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
              {alerts.map((a) => {
                const pos = districtPos(a.district)
                if (!pos) return null
                const color = COLOR[a.confidence] ?? COLOR.emerging
                return (
                  <CircleMarker key={a.cluster_id} center={pos} radius={alertRadius(a.report_count)}
                    pathOptions={{ color, fillColor: color, fillOpacity: 0.45 }}>
                    <Tooltip permanent direction="right" offset={[8, 0]}>{a.district}: {a.report_count}</Tooltip>
                    <Popup>{a.label}<br />{a.district}: {a.report_count} reports</Popup>
                  </CircleMarker>
                )
              })}
            </MapContainer>
          </div>

          <section className="panel" aria-labelledby="alerts-h">
            <h2 id="alerts-h" className="panel-title"><Icon name="alert" />Alerts</h2>
            {alerts.length === 0 ? <p className="muted">No alerts yet. Press "Replay demo wave".</p> : (
              <ul className="alerts">
                {alerts.map((a) => (
                  <li key={a.cluster_id} className="alert">
                    <h3>{a.label} in {a.district}</h3>
                    <div className="tags">
                      <span className={`tag ${a.confidence === 'confirmed' ? 'tag-red' : 'tag-amber'}`}>{a.confidence === 'confirmed' ? 'Confirmed' : 'Emerging'}</span>
                      <span className="tag tag-plain">{SCAM_TYPES[a.scam_type] ?? a.scam_type}</span>
                    </div>
                    <p className="stat-line">{a.report_count} reports from {a.distinct_reporters} people in {a.window_hours} hours</p>
                    <blockquote>Example: “{a.sample_text}”</blockquote>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </div>
    </>
  )
}
