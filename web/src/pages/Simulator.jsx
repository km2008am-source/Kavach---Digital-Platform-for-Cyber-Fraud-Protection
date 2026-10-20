import { useEffect, useRef, useState } from 'react'
import { simQuiz, simStart, simTurn } from '../api.js'
import TacticChip from '../components/TacticChip.jsx'
import ScoreCard from '../components/ScoreCard.jsx'

const HANGUP = 'I am hanging up and will call 1930 myself.'
const SR = typeof window !== 'undefined' ? window.SpeechRecognition || window.webkitSpeechRecognition : null

function speak(text, lang) {
  try {
    if (!('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(text)
    const want = lang === 'ta' ? 'ta-IN' : 'en-IN'
    u.lang = want
    const voices = window.speechSynthesis.getVoices()
    u.voice = voices.find((v) => v.lang === want) ?? voices.find((v) => v.lang.startsWith(lang)) ?? null
    window.speechSynthesis.speak(u)
  } catch { /* speech is optional */ }
}

export default function Simulator() {
  const [language, setLanguage] = useState('en')
  const [phase, setPhase] = useState('intro') // intro | prequiz | call | postquiz | done
  const [sess, setSess] = useState(null)
  const [answers, setAnswers] = useState([])
  const [thread, setThread] = useState([])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [sound, setSound] = useState(true)
  const [listening, setListening] = useState(false)
  const [result, setResult] = useState({ pre: null, post: null, final: null, debrief: '' })
  const endRef = useRef(null)

  useEffect(() => { endRef.current?.scrollIntoView?.({ block: 'end' }) }, [thread])
  useEffect(() => () => { try { window.speechSynthesis?.cancel() } catch { /* ignore */ } }, [])

  const reset = () => {
    setPhase('intro'); setSess(null); setAnswers([]); setThread([]); setDraft(''); setErr('')
    setResult({ pre: null, post: null, final: null, debrief: '' })
  }

  const start = async () => {
    setBusy(true); setErr('')
    const r = await simStart(language)
    setBusy(false)
    if (!r.ok) return setErr(r.message)
    setSess(r.data)
    setAnswers(r.data.quiz.map(() => ''))
    setThread([{ role: 'bot', text: r.data.bot_message, tactics: r.data.tactics }])
    setPhase('prequiz')
  }

  const submitQuiz = async (which) => {
    setBusy(true); setErr('')
    const r = await simQuiz(sess.session_id, which, answers)
    setBusy(false)
    if (!r.ok) return setErr(r.message)
    if (which === 'pre') {
      setResult((x) => ({ ...x, pre: r.data.score }))
      setAnswers(answers.map(() => ''))
      setPhase('call')
      if (sound) speak(thread[0].text, language)
    } else {
      setResult((x) => ({ ...x, post: r.data.score }))
      setPhase('done')
    }
  }

  const send = async (message) => {
    const msg = message.trim()
    if (!msg || busy) return
    setBusy(true); setErr(''); setDraft('')
    setThread((t) => [...t, { role: 'me', text: msg }])
    const r = await simTurn(sess.session_id, msg)
    setBusy(false)
    if (!r.ok) return setErr(r.message)
    const d = r.data
    setThread((t) => {
      const copy = [...t]
      copy[copy.length - 1] = { ...copy[copy.length - 1], score: d.user_turn_score }
      return [...copy, { role: 'bot', text: d.bot_message, tactics: d.tactics }]
    })
    if (sound) speak(d.bot_message, language)
    if (d.finished) {
      setResult((x) => ({ ...x, final: d.final_score, debrief: d.debrief ?? '' }))
      setPhase('postquiz')
    }
  }

  const listen = () => {
    if (!SR || listening) return
    const rec = new SR()
    rec.lang = language === 'ta' ? 'ta-IN' : 'en-IN'
    rec.onresult = (e) => setDraft(e.results[0][0].transcript)
    rec.onend = () => setListening(false)
    rec.onerror = () => setListening(false)
    setListening(true)
    rec.start()
  }

  const quizReady = answers.length > 0 && answers.every(Boolean)

  return (
    <>
      <h1>Practice a scam call</h1>
      <p className="muted">A fictional caller from a made-up agency. Nothing here is real, and nothing you type is stored with your name.</p>
      {err && (
        <p className="error" role="alert">
          {err} {phase !== 'intro' && <button type="button" className="secondary" onClick={reset}>Start over</button>}
        </p>
      )}

      {phase === 'intro' && (
        <section className="card">
          <p>You will answer four quick questions, take a short call, then answer the questions again. Never type real Aadhaar, card or OTP numbers.</p>
          <div className="row">
            <div>
              <label htmlFor="sl">Language</label>
              <select id="sl" value={language} onChange={(e) => setLanguage(e.target.value)}>
                <option value="en">English</option>
                <option value="ta">தமிழ்</option>
              </select>
            </div>
            <label className="row" style={{ margin: 0, fontWeight: 400 }}>
              <input type="checkbox" checked={sound} onChange={(e) => setSound(e.target.checked)} /> Speak the caller's lines aloud
            </label>
          </div>
          <p style={{ marginTop: '1rem' }}><button onClick={start} disabled={busy}>{busy ? 'Starting…' : 'Start'}</button></p>
        </section>
      )}

      {(phase === 'prequiz' || phase === 'postquiz') && sess && (
        <QuizCard sess={sess} answers={answers} setAnswers={setAnswers}
          title={phase === 'prequiz' ? 'Before the call' : 'After the call'}
          busy={busy} ready={quizReady} onSubmit={() => submitQuiz(phase === 'prequiz' ? 'pre' : 'post')} />
      )}

      {(phase === 'call' || phase === 'postquiz' || phase === 'done') && (
        <div className="phone" aria-label="Training simulation">
          <div className="phone-bar"><strong>Training simulation, fictional caller</strong><span>{phase === 'call' ? 'On call' : 'Call ended'}</span></div>
          <div className="thread" role="log" aria-live="polite">
            {thread.map((m, i) => (
              <div key={i} className={`msg msg-${m.role}`}>
                {m.role === 'bot' && m.tactics?.length > 0 && <div>{m.tactics.map((t) => <TacticChip key={t} code={t} lang={language} />)}</div>}
                <div>{m.text}</div>
                {m.role === 'me' && m.score != null && <div className="meter" title={`Resisted: ${m.score}/10`}><i style={{ width: `${m.score * 10}%` }} /></div>}
              </div>
            ))}
            <div ref={endRef} />
          </div>
          {phase === 'call' && (
            <form className="composer" onSubmit={(e) => { e.preventDefault(); send(draft) }}>
              <input type="text" aria-label="Your reply" value={draft} maxLength={500} onChange={(e) => setDraft(e.target.value)}
                placeholder={language === 'ta' ? 'உங்கள் பதிலை எழுதுங்கள்' : 'Type your reply'} />
              <div className="row">
                <button type="submit" disabled={busy || !draft.trim()}>Reply</button>
                {SR && <button type="button" className="secondary" onClick={listen} disabled={busy}>{listening ? 'Listening…' : 'Speak'}</button>}
                <button type="button" className="danger" onClick={() => send(HANGUP)} disabled={busy}>Hang up</button>
              </div>
            </form>
          )}
        </div>
      )}

      {phase === 'done' && (
        <>
          <ScoreCard pre={result.pre} post={result.post} final={result.final} debrief={result.debrief} />
          <button onClick={reset}>Try again</button>
        </>
      )}
    </>
  )
}

function QuizCard({ sess, answers, setAnswers, title, busy, ready, onSubmit }) {
  return (
    <section className="card">
      <h2>{title}</h2>
      {sess.quiz.map((q, i) => (
        <div key={q.id} className="quiz-q">
          <p><strong>{i + 1}.</strong> {q.q}</p>
          <div className="row">
            {['yes', 'no'].map((v) => (
              <label key={v} className="row" style={{ margin: 0, fontWeight: 400 }}>
                <input type="radio" name={`q${q.id}`} checked={answers[i] === v}
                  onChange={() => setAnswers(answers.map((a, j) => (j === i ? v : a)))} /> {v === 'yes' ? 'Yes' : 'No'}
              </label>
            ))}
          </div>
        </div>
      ))}
      <p style={{ marginTop: '1rem' }}><button onClick={onSubmit} disabled={busy || !ready}>{busy ? 'Saving…' : 'Continue'}</button></p>
    </section>
  )
}
