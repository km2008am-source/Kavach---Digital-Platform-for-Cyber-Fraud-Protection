import { ACTIONS, RISK_TEXT, SCAM_TYPES, riskTone } from '../constants.js'

export default function VerdictCard({ result }) {
  const tone = riskTone(result.risk_level)
  const links = result.links ?? []
  return (
    <section className={`card verdict verdict-${tone}`} aria-live="polite">
      <header>
        <span className={`pill pill-${tone}`}>{RISK_TEXT[result.risk_level] ?? result.risk_level}</span>
        <span className="muted">{SCAM_TYPES[result.scam_type] ?? result.scam_type} · score {result.risk_score}/100</span>
      </header>
      <p className="lead">{result.explanation_en}</p>
      {result.confidence === 'lower' && (
        <p className="note">Quick check only: the full AI check was not available, so treat this with extra care.</p>
      )}
      {result.red_flags?.length > 0 && (
        <>
          <h3>Why</h3>
          <ul className="flags">
            {result.red_flags.map((f) => <li key={f.code}>{f.label_en}</li>)}
          </ul>
        </>
      )}
      {links.map((l) => (
        <p key={l.url} className="muted">
          Link <code>{l.domain}</code>
          {l.lookalike_of && <> pretends to be <code>{l.lookalike_of}</code></>}
          {l.blocklisted && <> is on a known-bad list</>}
          {l.domain_age_days != null && <>, registered {l.domain_age_days} days ago</>}.
        </p>
      ))}
      {result.apk && (
        <p className="muted">
          App <code>{result.apk.app_name ?? result.apk.package ?? 'unknown'}</code> asks for {result.apk.permissions.length} permissions
          {result.apk.dangerous_combo && <strong> including a dangerous combination that can read your OTPs</strong>}.
        </p>
      )}
      <p className="action"><strong>What to do:</strong> {ACTIONS[result.recommended_action] ?? ''}</p>
      {result.risk_level !== 'low' && (
        <p className="note">If you have already paid or shared a code, dial <strong>1930</strong> right now.</p>
      )}
    </section>
  )
}
