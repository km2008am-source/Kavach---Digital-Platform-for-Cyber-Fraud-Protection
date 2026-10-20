import { NavLink, Route, Routes } from 'react-router-dom'
import Home from './pages/Home.jsx'
import Analyze from './pages/Analyze.jsx'
import Simulator from './pages/Simulator.jsx'
import Pulse from './pages/Pulse.jsx'
import Services from './pages/Services.jsx'
import News from './pages/News.jsx'

const LINKS = [
  ['/', 'Home'], ['/analyze', 'Check a message'], ['/simulator', 'Training'],
  ['/pulse', 'Scam Pulse'], ['/services', 'Get help'], ['/news', 'News'],
]

export default function App() {
  return (
    <>
      <header className="topbar">
        <div className="topbar-in">
          <NavLink to="/" className="brand">Kavach</NavLink>
          <nav className="nav" aria-label="Main">
            {LINKS.map(([to, label]) => (
              <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => (isActive ? 'active' : undefined)}>
                {label}
              </NavLink>
            ))}
          </nav>
          <a className="sos" href="tel:1930">Lost money? Dial 1930</a>
        </div>
      </header>
      <main>
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
      <footer>Kavach is a hackathon prototype. It helps you decide and report; it does not replace the police or your bank.</footer>
    </>
  )
}
