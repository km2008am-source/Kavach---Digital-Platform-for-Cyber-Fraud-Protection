import Icon from './Icon.jsx'

export default function ScoreCard({ pre, post, final, debrief }) {
  const lines = (debrief ?? '').split('\n').filter(Boolean)
  const delta = pre != null && post != null ? post - pre : null
  return (
    <section className="panel score-card" aria-live="polite">
      <h2>Your result</h2>
      <div className="scores">
        <Stat label="Resilience in the call" value={final} suffix="/100" main />
        <Stat label="Quiz before" value={pre} suffix="%" />
        <Stat label="Quiz after" value={post} suffix="%" />
      </div>
      {delta != null && (
        <p className={`notice ${delta >= 0 ? 'notice-ok' : 'notice-warn'}`}>
          <Icon name={delta >= 0 ? 'check' : 'info'} />
          {pre === 100 && post === 100 ? 'You already knew the answers. The real test is holding firm under pressure, as in the call above.' : delta > 0 ? `Up ${delta} points after training.` : delta === 0 ? 'Same as before. Try the call again.' : `Down ${-delta} points. Read the debrief and try again.`}
        </p>
      )}
      <h3>Debrief</h3>
      <ul className="debrief">
        {lines.map((l, i) => <li key={i}>{l}</li>)}
      </ul>
    </section>
  )
}

function Stat({ label, value, suffix, main }) {
  return (
    <div className={`score${main ? ' score-main' : ''}`}>
      <div className="score-n">{value ?? '–'}{value != null && <small>{suffix}</small>}</div>
      <div className="muted">{label}</div>
    </div>
  )
}
