import { Link } from 'react-router-dom'
import Icon from './Icon.jsx'

// Title band for inner pages: breadcrumb, page title and one line of what the page is for.
export default function PageHeader({ icon, title, children }) {
  return (
    <div className="page-head">
      <div className="wrap">
        <nav className="crumbs" aria-label="Breadcrumb">
          <Link to="/">Home</Link>
          <span aria-hidden="true">/</span>
          <span aria-current="page">{title}</span>
        </nav>
        <div className="page-title">
          {icon && <span className="page-icon"><Icon name={icon} size={26} /></span>}
          <div>
            <h1>{title}</h1>
            {children && <p className="page-intro">{children}</p>}
          </div>
        </div>
      </div>
    </div>
  )
}
