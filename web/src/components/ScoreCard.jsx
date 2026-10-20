export default function ScoreCard({ pre, post, final, debrief }) {
  const lines = (debrief ?? '').split('\n').filter(Boolean)
  const delta = pre != null && post != null ? post - pre : null
  return (
    <section className="card score" aria-live="polite">
      <div className="score-grid">
        <Stat label="Quiz before" value={pre} suffix="%" />
        <Stat label="Quiz after" value={post} suffix="%" />
        <Stat label="Resilience in the call" value={final} suffix="/100" big />
      </div>
      {delta != null && (
        <p className={delta >= 0 ? 'good' : 'warn'}>
          {pre === 100 && post === 100 ? 'You already knew the answers. The real test is holding firm under pressure, as in the call above.' : delta > 0 ? `Up ${delta} points after training.` : delta === 0 ? 'Same as before. Try the call again.' : `Down ${-delta} points. Read the debrief and try again.`}
        </p>
      )}
      <h3>Debrief</h3>
      <ul className="flags">
        {lines.map((l, i) => <li key={i}>{l}</li>)}
      </ul>
    </section>
  )
}

function Stat({ label, value, suffix, big }) {
  return (
    <div className={`stat ${big ? 'stat-big' : ''}`}>
      <div className="stat-n">{value ?? '–'}{value != null && <small>{suffix}</small>}</div>
      <div className="muted">{label}</div>
    </div>
  )
}
