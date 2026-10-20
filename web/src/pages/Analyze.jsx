import { useRef, useState } from 'react'
import { analyzeFile, analyzeText } from '../api.js'
import { SAMPLE_KYC } from '../constants.js'
import VerdictCard from '../components/VerdictCard.jsx'
import DemoBadge from '../components/DemoBadge.jsx'

const MAX_MB = 20

export default function Analyze() {
  const [text, setText] = useState('')
  const [file, setFile] = useState(null)
  const [language, setLanguage] = useState('en')
  const [busy, setBusy] = useState(false)
  const [out, setOut] = useState(null)
  const fileRef = useRef(null)

  const pick = (f) => {
    if (f && f.size > MAX_MB * 1024 * 1024) {
      setOut({ ok: false, message: `That file is larger than ${MAX_MB} MB.` })
      if (fileRef.current) fileRef.current.value = ''
      return
    }
    setFile(f ?? null)
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
      <h1>Check a message</h1>
      <p className="muted">Works like forwarding to Kavach on WhatsApp. Nothing you add here is kept.</p>
      <form className="card" onSubmit={submit}>
        <label htmlFor="msg">Message or link</label>
        <textarea id="msg" value={text} onChange={(e) => setText(e.target.value)} maxLength={5000}
          placeholder="Paste the SMS, WhatsApp message or link here" />
        <div className="row" style={{ marginTop: '.75rem' }}>
          <div>
            <label htmlFor="file">Screenshot or app file (optional)</label>
            <input id="file" ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp,.apk"
              onChange={(e) => pick(e.target.files?.[0])} />
          </div>
          <div>
            <label htmlFor="lang">Language</label>
            <select id="lang" value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="en">English</option>
              <option value="ta">தமிழ்</option>
            </select>
          </div>
        </div>
        <div className="row" style={{ marginTop: '1rem' }}>
          <button type="submit" disabled={busy}>{busy ? 'Checking…' : 'Check it'}</button>
          <button type="button" className="secondary" onClick={() => { setText(SAMPLE_KYC); setFile(null); setOut(null) }}>
            Try a sample scam
          </button>
        </div>
      </form>
      {out && !out.ok && <p className="error" role="alert">{out.message}</p>}
      {out?.ok && (
        <>
          {out.demo && <DemoBadge>Example only: the server could not be reached, so this is a sample result, not a check of what you entered.</DemoBadge>}
          <VerdictCard result={out.data} />
        </>
      )}
    </>
  )
}
