import { ACTIONS, HI, RISK_TEXT, SCAM_TYPES, riskTone } from '../constants.js'
import Icon from './Icon.jsx'

const BAND_ICON = { red: 'alert', amber: 'alert', green: 'check' }

// lang="hi" shows the card's own words in Hindi; text missing from HI falls back to English.
export default function VerdictCard({ result, lang = 'en' }) {
  const hi = lang === 'hi'
  const tone = riskTone(result.risk_level)
  const links = result.links ?? []
  const flags = result.red_flags ?? []
  const score = Math.max(0, Math.min(100, Number(result.risk_score) || 0))
  const hasEvidence = links.length > 0 || result.apk
  const riskText = (hi && HI.risk[result.risk_level]) || RISK_TEXT[result.risk_level] || result.risk_level
  const typeText = (hi && HI.types[result.scam_type]) || SCAM_TYPES[result.scam_type] || result.scam_type
  const action = (hi && HI.actions[result.recommended_action]) || ACTIONS[result.recommended_action] || ''

  return (
    <section className={`verdict verdict-${tone}`} aria-live="polite" aria-label="Result" lang={hi ? 'hi' : undefined}>
      <div className="verdict-band">
        <Icon name={BAND_ICON[tone]} size={34} />
        <div>
          <div className="verdict-level">{riskText}</div>
          <div className="verdict-type">{typeText}</div>
        </div>
        <div className="verdict-score"><b>{score}</b><span>{hi ? HI.ui.scoreOf : 'risk score out of 100'}</span></div>
      </div>
      <div className="meter" role="img" aria-label={`Risk score ${score} out of 100`}><i style={{ width: `${score}%` }} /></div>

      <div className="verdict-body">
        <p className="verdict-explain">{result.explanation_en}</p>
        {result.confidence === 'lower' && (
          <p className="notice notice-warn"><Icon name="info" />{hi ? HI.ui.lower : 'Quick check only: the full AI check was not available, so treat this with extra care.'}</p>
        )}

        {(flags.length > 0 || hasEvidence) && (
          <div className="verdict-cols">
            {flags.length > 0 && (
              <div>
                <h3>{hi ? HI.ui.why : 'Why'}</h3>
                <ul className="reasons">
                  {flags.map((f) => <li key={f.code}><Icon name="alert" size={18} /><span>{(hi && HI.flags[f.code]) || f.label_en}</span></li>)}
                </ul>
              </div>
            )}
            {hasEvidence && (
              <div lang="en">
                <h3>{hi ? HI.ui.found : 'What we found'}</h3>
                {links.map((l) => (
                  <p key={l.url} className="evidence-row">
                    <Icon name="link" size={18} />
                    <span>
                      Link <code>{l.domain}</code>
                      {l.lookalike_of && <> pretends to be <code>{l.lookalike_of}</code></>}
                      {l.blocklisted && <> is on a known-bad list</>}
                      {l.domain_age_days != null && <>, registered {l.domain_age_days} days ago</>}.
                    </span>
                  </p>
                ))}
                {result.apk && (
                  <p className="evidence-row">
                    <Icon name="app" size={18} />
                    <span>
                      App <code>{result.apk.app_name ?? result.apk.package ?? 'unknown'}</code> asks for {result.apk.permissions.length} permissions
                      {result.apk.dangerous_combo && <strong> including a dangerous combination that can read your OTPs</strong>}.
                    </span>
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        <div className="todo">
          <p><strong>{hi ? HI.ui.todo : 'What to do:'}</strong> {action}</p>
          <div className="btn-row">
            {result.recommended_action === 'report_chakshu' && (
              <a className="btn btn-ghost" href="https://sancharsaathi.gov.in" target="_blank" rel="noopener noreferrer">
                <Icon name="external" size={18} />{hi ? HI.ui.report : 'Report on Sanchar Saathi'}
              </a>
            )}
            {result.risk_level !== 'low' && <a className="btn btn-saffron" href="tel:1930"><Icon name="phone" size={18} />{hi ? HI.ui.dial : 'Dial 1930'}</a>}
          </div>
        </div>
        {result.risk_level !== 'low' && (
          <p className="small muted" style={{ margin: '.8rem 0 0' }}>
            {hi ? HI.ui.paid : <>If you have already paid or shared a code, dial <strong>1930</strong> right now.</>}
          </p>
        )}
      </div>
    </section>
  )
}
