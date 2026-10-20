export default function DemoBadge({ children = 'Demo data: the live server could not be reached' }) {
  return <p className="demo-badge" role="status">{children}</p>
}
