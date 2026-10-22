import { useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { analyzeFile, analyzeText } from '../api.js'
import { SAMPLE_KYC } from '../constants.js'
import VerdictCard from '../components/VerdictCard.jsx'
import DemoBadge from '../components/DemoBadge.jsx'
import PageHeader from '../components/PageHeader.jsx'
import Icon from '../components/Icon.jsx'

const MAX_MB = 20

export default function Analyze() {
  const { state } = useLocation()
  const [text, setText] = useState(state?.text ?? '')       // carried over from the Home page box
  const [file, setFile] = useState(null)
  const [language, setLanguage] = useState('en')
  const [busy, setBusy] = useState(false)
  const [out, setOut] = useState(null)
  const [over, setOver] = useState(false)
  const fileRef = useRef(null)

  const pick = (f) => {
    if (f && f.size > MAX_MB * 1024 * 1024) {
      setOut({ ok: false, message: `That file is larger than ${MAX_MB} MB.` })
      if (fileRef.current) fileRef.current.value = ''
      return
    }
    setFile(f ?? null)
  }

  const clearFile = () => {
    setFile(null)
    if (fileRef.current) fileRef.current.value = ''
  }

  const submit = async (e) => {
    e.preventDefault()
    if (busy) return
    if (!text.trim() && !file) {
      setOut({ ok: false, message: 'Paste a message or link, or add a screenshot or app file first.' })
      return
    }
    setBusy(true)
    setOut(null)
    setOut(file ? await analyzeFile(file, text.trim(), language) : await analyzeText(text.trim(), language))
    setBusy(false)
  }

  return (
    <>
      <PageHeader icon="message" title="Check a message">
        Works like forwarding to Kavach on WhatsApp. Nothing you add here is kept.
      </PageHeader>

      <div className="wrap page-body">
        <div className="check-grid">
          <div>
            <form className="panel" onSubmit={submit}>
              <div className="field">
                <label htmlFor="msg">Message or link</label>
                <p className="hint" id="msg-hint">Paste the SMS, WhatsApp message or link exactly as you received it.</p>
                <textarea id="msg" aria-describedby="msg-hint" value={text} onChange={(e) => setText(e.target.value)} maxLength={5000}
                  placeholder="Paste the SMS, WhatsApp message or link here" />
              </div>

              <div className="field">
                <span className="label" id="file-label">Screenshot or app file (optional)</span>
                <div className={`drop${over ? ' over' : ''}`}
                  onDragEnter={() => setOver(true)} onDragLeave={() => setOver(false)} onDrop={() => setOver(false)}>
                  <span className="drop-icon"><Icon name="upload" size={22} /></span>
                  <div>
                    <strong>Choose a file or drag it here</strong>
                    <span>PNG, JPG or WebP screenshot, or an Android app file (.apk). Up to {MAX_MB} MB.</span>
                  </div>
                  <input id="file" ref={fileRef} type="file" aria-labelledby="file-label" accept="image/png,image/jpeg,image/webp,.apk"
                    onChange={(e) => pick(e.target.files?.[0])} />
                </div>
                {file && (
                  <span className="file-chip">
                    <Icon name={file.name.toLowerCase().endsWith('.apk') ? 'app' : 'upload'} size={16} />
                    {file.name}
                    <button type="button" className="btn-ghost" onClick={clearFile} aria-label={`Remove ${file.name}`}>Remove</button>
                  </span>
                )}
              </div>

              <fieldset className="field" style={{ border: 0, padding: 0, margin: '0 0 1.4rem' }}>
                <legend className="label">Language of the result</legend>
                <div className="seg">
                  <label><input type="radio" name="lang" value="en" checked={language === 'en'} onChange={() => setLanguage('en')} />English</label>
                  <label lang="ta"><input type="radio" name="lang" value="ta" checked={language === 'ta'} onChange={() => setLanguage('ta')} />தமிழ்</label>
                </div>
              </fieldset>

              <div className="btn-row">
                <button type="submit" disabled={busy}><Icon name="shield" />{busy ? 'Checking…' : 'Check it'}</button>
                <button type="button" className="btn-ghost" onClick={() => { setText(SAMPLE_KYC); clearFile(); setOut(null) }}>
                  Try a sample scam
                </button>
              </div>
            </form>

            <div aria-live="polite">
              {out && !out.ok && <p className="notice notice-error" role="alert" style={{ marginTop: '1.25rem' }}><Icon name="alert" />{out.message}</p>}
              {out?.ok && (
                <div style={{ marginTop: '1.25rem' }}>
                  {out.demo && <DemoBadge>Example only: the server could not be reached, so this is a sample result, not a check of what you entered.</DemoBadge>}
                  <VerdictCard result={out.data} />
                </div>
              )}
            </div>
          </div>

          <aside className="panel aside">
            <h2 className="panel-title"><Icon name="info" />What Kavach checks</h2>
            <ul>
              <li>Pressure words: arrest threats, “today only”, OTP or PIN requests</li>
              <li>Links that pretend to be your bank or a government site</li>
              <li>Screenshots, read the same way as text</li>
              <li>Android apps that can read your SMS and steal OTPs</li>
            </ul>
            <h2 className="panel-title"><Icon name="lock" />Never share</h2>
            <p className="small muted">No bank, police officer or government office will ever ask for your OTP, UPI PIN or card number on a call or message.</p>
            <a className="btn btn-saffron" href="tel:1930" style={{ width: '100%' }}><Icon name="phone" />Lost money? Dial 1930</a>
          </aside>
        </div>
      </div>
    </>
  )
}
