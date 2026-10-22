import { useEffect, useRef, useState } from 'react'
import { simQuiz, simStart, simTurn } from '../api.js'
import { TACTICS } from '../constants.js'
import TacticChip from '../components/TacticChip.jsx'
import ScoreCard from '../components/ScoreCard.jsx'
import PageHeader from '../components/PageHeader.jsx'
import Icon from '../components/Icon.jsx'

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

  const STEPS = [['prequiz', 'Before the call'], ['call', 'Take the call'], ['postquiz', 'After the call'], ['done', 'Your result']]
  const at = STEPS.findIndex(([p]) => p === phase)
  const stepClass = (i) => (at < 0 ? undefined : i < at ? 'done' : i === at ? 'now' : undefined)

  return (
    <>
      <PageHeader icon="training" title="Practice a scam call">
        A fictional caller from a made-up agency. Nothing here is real, and nothing you type is stored with your name.
      </PageHeader>

      <div className="wrap page-body">
        <ol className="steps" aria-label="Progress">
          {STEPS.map(([p, label], i) => (
            <li key={p} className={stepClass(i)} aria-current={i === at ? 'step' : undefined}>{label}</li>
          ))}
        </ol>

        {err && (
          <div className="notice notice-error" role="alert">
            <Icon name="alert" />
            <span>{err} {phase !== 'intro' && <button type="button" className="btn-ghost" style={{ marginLeft: '.5rem', padding: '.2rem .7rem' }} onClick={reset}>Start over</button>}</span>
          </div>
        )}

        <div className="sim-grid">
          <div>
            {phase === 'intro' && (
              <section className="panel">
                <h2>How it works</h2>
                <p>You will answer four quick questions, take a short call, then answer the questions again. Never type real Aadhaar, card or OTP numbers.</p>
                <fieldset className="field" style={{ border: 0, padding: 0, margin: '0 0 1rem' }}>
                  <legend className="label">Language</legend>
                  <div className="seg">
                    <label><input type="radio" name="sl" value="en" checked={language === 'en'} onChange={() => setLanguage('en')} />English</label>
                    <label lang="ta"><input type="radio" name="sl" value="ta" checked={language === 'ta'} onChange={() => setLanguage('ta')} />தமிழ்</label>
                  </div>
                </fieldset>
                <label style={{ display: 'flex', alignItems: 'center', gap: '.5rem', fontWeight: 600 }}>
                  <input type="checkbox" checked={sound} onChange={(e) => setSound(e.target.checked)} style={{ width: '1.2rem', height: '1.2rem' }} />
                  <Icon name="volume" size={18} />Speak the caller's lines aloud
                </label>
                <p style={{ margin: '1.2rem 0 0' }}><button onClick={start} disabled={busy}><Icon name="phone" />{busy ? 'Starting…' : 'Start'}</button></p>
              </section>
            )}

            {(phase === 'prequiz' || phase === 'postquiz') && sess && (
              <QuizCard sess={sess} answers={answers} setAnswers={setAnswers}
                title={phase === 'prequiz' ? 'Before the call' : 'After the call'}
                busy={busy} ready={quizReady} onSubmit={() => submitQuiz(phase === 'prequiz' ? 'pre' : 'post')} />
            )}

            {(phase === 'call' || phase === 'postquiz' || phase === 'done') && (
              <div className="call" aria-label="Training simulation" style={{ marginTop: phase === 'call' ? 0 : '1.25rem' }}>
                <div className="call-head">
                  <span className="call-avatar"><Icon name="user" size={22} /></span>
                  <span className="call-who"><strong>Unknown caller</strong><span>Training simulation, fictional caller</span></span>
                  <span className={`call-state${phase === 'call' ? '' : ' ended'}`}>{phase === 'call' ? 'On call' : 'Call ended'}</span>
                </div>
                <div className="thread" role="log" aria-live="polite">
                  {thread.map((m, i) => (
                    <div key={i} className={`msg msg-${m.role}`}>
                      {m.role === 'bot' && m.tactics?.length > 0 && <div>{m.tactics.map((t) => <TacticChip key={t} code={t} lang={language} />)}</div>}
                      <div>{m.text}</div>
                      {m.role === 'me' && m.score != null && (
                        <div className="resist" title={`Resisted: ${m.score}/10`}>Resisted <i><b style={{ width: `${m.score * 10}%` }} /></i> {m.score}/10</div>
                      )}
                    </div>
                  ))}
                  <div ref={endRef} />
                </div>
                {phase === 'call' && (
                  <form className="composer" onSubmit={(e) => { e.preventDefault(); send(draft) }}>
                    <input type="text" aria-label="Your reply" value={draft} maxLength={500} onChange={(e) => setDraft(e.target.value)}
                      placeholder={language === 'ta' ? 'உங்கள் பதிலை எழுதுங்கள்' : 'Type your reply'} />
                    <div className="btn-row">
                      <button type="submit" disabled={busy || !draft.trim()}><Icon name="send" size={18} />Reply</button>
                      {SR && <button type="button" className="btn-ghost" onClick={listen} disabled={busy}><Icon name="mic" size={18} />{listening ? 'Listening…' : 'Speak'}</button>}
                      <button type="button" className="btn-danger" onClick={() => send(HANGUP)} disabled={busy}><Icon name="hangup" size={18} />Hang up</button>
                    </div>
                  </form>
                )}
              </div>
            )}

            {phase === 'done' && (
              <div style={{ marginTop: '1.25rem' }}>
                <ScoreCard pre={result.pre} post={result.post} final={result.final} debrief={result.debrief} />
                <button onClick={reset} style={{ marginTop: '1rem' }}><Icon name="replay" />Try again</button>
              </div>
            )}
          </div>

          <aside className="panel aside">
            <h2 className="panel-title"><Icon name="alert" />Pressure tactics to spot</h2>
            <p className="small muted">The caller uses these on you. Each one is named as it happens.</p>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {Object.entries(TACTICS).map(([code, t]) => (
                <li key={code} style={{ marginBottom: '.6rem' }}>
                  <TacticChip code={code} lang={language} />
                  <span className="small" style={{ display: 'block', color: 'var(--ink-2)' }}>{t.hint}</span>
                </li>
              ))}
            </ul>
          </aside>
        </div>
      </div>
    </>
  )
}

function QuizCard({ sess, answers, setAnswers, title, busy, ready, onSubmit }) {
  return (
    <section className="panel">
      <h2>{title}</h2>
      <p className="small muted">Answer yes or no. There is no penalty for a wrong answer.</p>
      {sess.quiz.map((q, i) => (
        <fieldset key={q.id} className="quiz-q" style={{ border: 0, margin: 0, borderBottom: '1px solid var(--line-2)' }}>
          <legend style={{ padding: 0, marginBottom: '.5rem' }}><strong>{i + 1}.</strong> {q.q}</legend>
          <div className="seg">
            {['yes', 'no'].map((v) => (
              <label key={v}>
                <input type="radio" name={`q${q.id}`} checked={answers[i] === v}
                  onChange={() => setAnswers(answers.map((a, j) => (j === i ? v : a)))} />{v === 'yes' ? 'Yes' : 'No'}
              </label>
            ))}
          </div>
        </fieldset>
      ))}
      <p style={{ margin: '1.2rem 0 0' }}><button onClick={onSubmit} disabled={busy || !ready}>{busy ? 'Saving…' : 'Continue'}</button></p>
    </section>
  )
}
