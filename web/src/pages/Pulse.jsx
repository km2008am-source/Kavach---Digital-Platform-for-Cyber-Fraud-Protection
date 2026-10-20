import { useCallback, useEffect, useState } from 'react'
import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { pulseAlerts, pulseReplay } from '../api.js'
import { SCAM_TYPES, alertRadius, districtPos } from '../constants.js'
import DemoBadge from '../components/DemoBadge.jsx'

const POLL_MS = 5000

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
      <h1>Scam Pulse</h1>
      <p className="muted">Anonymous reports are grouped by wording to spot a scam wave early. <strong>This page runs on a seeded replay, not real national data.</strong></p>
      {res?.demo && <DemoBadge />}
      <div className="row" style={{ margin: '.5rem 0' }}>
        <button onClick={replay}>Replay demo wave</button>
        {msg && <span role="status">{msg}</span>}
      </div>
      {res && !res.ok && <p className="error" role="alert">{res.message}</p>}
      <div className="map">
        <MapContainer center={[10.9, 78.4]} zoom={7} style={{ height: '100%', width: '100%' }} scrollWheelZoom={false}>
          <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {alerts.map((a) => {
            const pos = districtPos(a.district)
            if (!pos) return null
            const color = a.confidence === 'confirmed' ? '#b42318' : '#d98a0b'
            return (
              <CircleMarker key={a.cluster_id} center={pos} radius={alertRadius(a.report_count)}
                pathOptions={{ color, fillColor: color, fillOpacity: 0.45 }}>
                <Tooltip permanent direction="right" offset={[8, 0]}>{a.district} · {a.report_count}</Tooltip>
                <Popup>{a.label}<br />{a.district}: {a.report_count} reports</Popup>
              </CircleMarker>
            )
          })}
        </MapContainer>
      </div>
      <section className="card">
        <h2>Alerts</h2>
        {alerts.length === 0 ? <p className="muted">No alerts yet. Press "Replay demo wave".</p> : (
          <ul className="alert-list">
            {alerts.map((a) => (
              <li key={a.cluster_id}>
                <strong>{a.label}</strong> in {a.district}{' '}
                <span className={`pill pill-${a.confidence === 'confirmed' ? 'red' : 'amber'}`}>{a.confidence}</span>
                <div className="muted">{a.report_count} reports from {a.distinct_reporters} people in {a.window_hours} h · {SCAM_TYPES[a.scam_type] ?? a.scam_type}</div>
                <div className="muted">Example: “{a.sample_text}”</div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  )
}
