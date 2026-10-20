import { Link } from 'react-router-dom'

const TILES = [
  ['/analyze', 'Check a message', 'Paste a message or link, or add a screenshot or app file. Get a verdict and the reasons in plain words.'],
  ['/simulator', 'Practice a scam call', 'A fictional "officer" uses real pressure tactics. Each one is named as it happens, then you get a score.'],
  ['/pulse', 'Scam Pulse', 'See where a scam wave is building. Demo data from a seeded replay.'],
  ['/services', 'Get help', 'The right government service for your situation, with official links.'],
  ['/news', 'Scam news', 'Recent reports, with a link to every source.'],
]

export default function Home() {
  return (
    <>
      <section className="hero">
        <h1>One place that protects you before, during and after a scam.</h1>
        <p>On WhatsApp, Kavach screens calls and checks messages. This website is the training ground and the dashboard behind it.</p>
        <p><a className="btn" href="tel:1930">If you already paid: dial 1930 now</a></p>
      </section>
      <div className="grid">
        {TILES.map(([to, title, text]) => (
          <Link key={to} to={to} className="card tile">
            <h2>{title}</h2>
            <p>{text}</p>
          </Link>
        ))}
      </div>
    </>
  )
}
