import Icon from './Icon.jsx'

export default function DemoBadge({ children = 'Demo data: the live server could not be reached' }) {
  return <p className="notice notice-info" role="status"><Icon name="info" />{children}</p>
}
