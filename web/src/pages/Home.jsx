import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Icon from '../components/Icon.jsx'

// Before, during and after a scam: a real sequence, so the stages are numbered.
const STAGES = [
  {
    n: 1, when: 'Before', title: 'Learn the tricks',
    text: 'Know the pressure tactics before a scammer uses them on you.',
    links: [
      ['/simulator', 'training', 'Practice a scam call', 'A fictional "officer" uses real pressure tactics. Each one is named as it happens, then you get a score.'],
      ['/news', 'news', 'Scam news', 'Recent reports, with a link to every source.'],
      ['/pulse', 'pulse', 'Scam Pulse', 'See where a scam wave is building. Demo data from a seeded replay.'],
    ],
  },
  {
    n: 2, when: 'During', title: 'Check before you act',
    text: 'Got a message, link, screenshot or app you are not sure about? Check it first.',
    links: [
      ['/analyze', 'message', 'Check a message', 'Paste a message or link, or add a screenshot or app file. Get a verdict and the reasons in plain words.'],
    ],
  },
  {
    n: 3, when: 'After', title: 'Get help fast',
    text: 'If money or an OTP has gone, the first hour matters most.',
    links: [
      ['/services', 'help', 'Get help', 'The right government service for your situation, with official links.'],
    ],
  },
]

export default function Home() {
  const [text, setText] = useState('')
  const navigate = useNavigate()

  const check = (e) => {
    e.preventDefault()
    navigate('/analyze', { state: { text: text.trim() } })
  }

  return (
    <>
      <section className="hero">
        <div className="wrap hero-grid">
          <div>
            <h1>Got a suspicious call or message? Check it before you act.</h1>
            <p className="hero-lead">
              Kavach looks at messages, links, screenshots and app files and tells you, in plain words, whether they look like a scam.
              On WhatsApp it also screens calls. This website is the training ground and the dashboard behind it.
            </p>
            <form className="quick panel" onSubmit={check}>
              <label htmlFor="quick">Paste the message or link</label>
              <textarea id="quick" value={text} onChange={(e) => setText(e.target.value)} maxLength={5000}
                placeholder="For example: Your bank account will be blocked today. Update KYC at…" />
              <div className="btn-row">
                <button type="submit"><Icon name="message" />Check this message</button>
                <Link className="btn btn-ghost" to="/analyze"><Icon name="upload" />Upload a screenshot or app</Link>
              </div>
            </form>
          </div>

          <aside className="sos-panel" aria-labelledby="sos-h">
            <h2 id="sos-h">Already paid or shared an OTP?</h2>
            <a className="sos-num" href="tel:1930" aria-label="Call 1930, National Cyber Crime Helpline">1930</a>
            <p>Call the National Cyber Crime Helpline now. Your chance of getting money back is highest in the first hour.</p>
            <ol className="sos-steps">
              <li><span>Call 1930 and give the transaction ID, amount and time.</span></li>
              <li><span>File the full complaint on <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer">cybercrime.gov.in</a>.</span></li>
              <li><span>Ask your bank to freeze the transaction.</span></li>
            </ol>
            <p style={{ margin: '1rem 0 0' }}><Link to="/services" className="btn btn-saffron">See all official help</Link></p>
          </aside>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="section-head">
            <h2>Protection before, during and after a scam</h2>
            <p>Scams work through pressure and speed. Kavach helps you slow down at each moment.</p>
          </div>
          <div className="stages">
            {STAGES.map((s) => (
              <div key={s.n} className="stage">
                <span className="stage-n">{s.n}. {s.when}</span>
                <h3>{s.title}</h3>
                <p>{s.text}</p>
                <ul className="stage-links">
                  {s.links.map(([to, icon, title, desc]) => (
                    <li key={to}>
                      <Link to={to}>
                        <Icon name={icon} size={22} />
                        <span><strong>{title}</strong><span>{desc}</span></span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <div className="wrap trust">
          <div>
            <Icon name="lock" size={22} />
            <div><strong>Private by design</strong><p>Messages and files are checked, not kept with your name.</p></div>
          </div>
          <div>
            <Icon name="check" size={22} />
            <div><strong>Official links only</strong><p>Every service points to the government or regulator's own website.</p></div>
          </div>
          <div>
            <Icon name="globe" size={22} />
            <div><strong>English and தமிழ்</strong><p>Check messages and practise calls in Tamil or English.</p></div>
          </div>
        </div>
      </section>
    </>
  )
}
