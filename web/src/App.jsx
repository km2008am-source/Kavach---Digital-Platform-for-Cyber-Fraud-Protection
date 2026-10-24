import { useEffect, useState } from 'react'
import { Link, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import Home from './pages/Home.jsx'
import Analyze from './pages/Analyze.jsx'
import Simulator from './pages/Simulator.jsx'
import Pulse from './pages/Pulse.jsx'
import Services from './pages/Services.jsx'
import News from './pages/News.jsx'
import Icon from './components/Icon.jsx'

const LINKS = [
  ['/', 'Home', 'shield'], ['/analyze', 'Check a message', 'message'], ['/simulator', 'Training', 'training'],
  ['/pulse', 'Scam Pulse', 'pulse'], ['/services', 'Get help', 'help'], ['/news', 'News', 'news'],
]

const SIZES = [['sm', 'A−', 'Smaller text'], ['md', 'A', 'Normal text'], ['lg', 'A+', 'Larger text']]

function readSize() {
  try { return localStorage.getItem('kavach-text-size') || 'md' } catch { return 'md' }
}

export default function App() {
  const [size, setSize] = useState(readSize)
  const [menuOpen, setMenuOpen] = useState(false)
  const { pathname } = useLocation()

  useEffect(() => {
    document.documentElement.dataset.textSize = size
    try { localStorage.setItem('kavach-text-size', size) } catch { /* private mode: size just resets */ }
  }, [size])

  // A new page starts at the top (the menu closes in the link's own click handler).
  useEffect(() => { window.scrollTo?.(0, 0) }, [pathname])

  return (
    <>
      <div className="tricolour" aria-hidden="true"><i /><i /><i /></div>
      <div className="utility">
        <div className="wrap utility-in">
          <a className="skip" href="#main">Skip to main content</a>
          <div className="text-size" role="group" aria-label="Text size">
            <span className="utility-label">Text size</span>
            {SIZES.map(([key, label, title]) => (
              <button key={key} type="button" className={size === key ? 'on' : undefined} aria-pressed={size === key}
                title={title} onClick={() => setSize(key)}>{label}</button>
            ))}
          </div>
        </div>
      </div>

      <header className="masthead">
        <div className="wrap masthead-in">
          <Link to="/" className="brand" aria-label="Kavach home">
            <svg className="brand-mark" viewBox="0 0 32 32" aria-hidden="true">
              <path d="M16 2.5 27 7v8.2c0 7-4.6 12.6-11 14.3C9.6 27.8 5 22.2 5 15.2V7z" fill="#12305E" />
              <path d="M16 6.4 23.4 9.4v5.9c0 4.9-3.1 8.9-7.4 10.3-4.3-1.4-7.4-5.4-7.4-10.3V9.4z" fill="#fff" />
              <path d="M16 9.6 20.2 11.3v4c0 3-1.8 5.4-4.2 6.4-2.4-1-4.2-3.4-4.2-6.4v-4z" fill="#E46F12" />
            </svg>
            <span className="brand-text">
              <span className="brand-name">Kavach</span>
              <span className="brand-sub">Cyber fraud help for every Indian</span>
              <span className="brand-sub hi" lang="hi">साइबर धोखाधड़ी से सुरक्षा</span>
            </span>
          </Link>
          <a className="helpline" href="tel:1930">
            <span className="helpline-icon"><Icon name="phone" size={22} /></span>
            <span>
              <span className="helpline-top">Lost money? Dial</span>
              <span className="helpline-num">1930</span>
              <span className="helpline-sub">National Cyber Crime Helpline</span>
            </span>
          </a>
        </div>
      </header>

      <nav className="navband" aria-label="Main">
        <div className="wrap navband-in">
          <button type="button" className="menu-btn" aria-expanded={menuOpen} aria-controls="main-menu"
            onClick={() => setMenuOpen((o) => !o)}>
            Menu
          </button>
          <ul id="main-menu" className={menuOpen ? 'open' : undefined}>
            {LINKS.map(([to, label, icon]) => (
              <li key={to}>
                <NavLink to={to} end={to === '/'} className={({ isActive }) => (isActive ? 'active' : undefined)}
                  onClick={() => setMenuOpen(false)}>
                  <Icon name={icon} size={18} />{label}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      </nav>

      <main id="main" tabIndex={-1}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/simulator" element={<Simulator />} />
          <Route path="/pulse" element={<Pulse />} />
          <Route path="/services" element={<Services />} />
          <Route path="/news" element={<News />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </main>

      <footer className="site-foot">
        <div className="wrap foot-grid">
          <div>
            <p className="foot-brand">Kavach</p>
            <p>Check suspicious messages, practise saying no to scam calls, and reach the right official help fast.</p>
          </div>
          <div>
            <p className="foot-head">Use Kavach</p>
            <ul>
              {LINKS.slice(1).map(([to, label]) => <li key={to}><Link to={to}>{label}</Link></li>)}
            </ul>
          </div>
          <div>
            <p className="foot-head">Official help</p>
            <ul>
              <li><a href="tel:1930">Cyber crime helpline: 1930</a></li>
              <li><a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer">cybercrime.gov.in</a></li>
              <li><a href="https://sancharsaathi.gov.in" target="_blank" rel="noopener noreferrer">sancharsaathi.gov.in</a></li>
            </ul>
          </div>
        </div>
        <div className="foot-note">
          <div className="wrap">
            Kavach is a hackathon prototype, not an official Government of India service. It helps you decide and report;
            it does not replace the police or your bank.
          </div>
        </div>
      </footer>
    </>
  )
}
