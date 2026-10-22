// Small stroke icons (24x24). Decorative by default; pass `label` when an icon stands alone.
const PATHS = {
  shield: <path d="M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6l7-3z" />,
  phone: <path d="M5 4h3l2 5-2.5 1.5a11 11 0 0 0 5 5L14 13l5 2v3a2 2 0 0 1-2 2A15 15 0 0 1 3 6a2 2 0 0 1 2-2z" />,
  message: <><path d="M4 5h16v11H9l-5 4V5z" /><path d="M8 9h8M8 12h5" /></>,
  training: <><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1.2" /></>,
  pulse: <path d="M3 12h4l3-7 4 14 3-7h4" />,
  help: <><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="4" /><path d="M5.6 5.6l3.6 3.6M14.8 14.8l3.6 3.6M18.4 5.6l-3.6 3.6M9.2 14.8l-3.6 3.6" /></>,
  news: <><path d="M4 5h13v14H6a2 2 0 0 1-2-2V5z" /><path d="M17 8h3v9a2 2 0 0 1-2 2" /><path d="M7.5 9h6M7.5 12.5h6M7.5 16h4" /></>,
  alert: <><path d="M12 3.5l9.5 16.5h-19L12 3.5z" /><path d="M12 10v4.5M12 17.2v.1" /></>,
  check: <><circle cx="12" cy="12" r="9" /><path d="M8 12.3l2.8 2.8L16.2 9" /></>,
  link: <><path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1" /><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1" /></>,
  app: <><rect x="7" y="3" width="10" height="18" rx="2" /><path d="M11 18h2" /></>,
  upload: <><path d="M12 15V4M8 8l4-4 4 4" /><path d="M4 15v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4" /></>,
  lock: <><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></>,
  globe: <><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" /></>,
  external: <><path d="M14 4h6v6M20 4l-9 9" /><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" /></>,
  mic: <><rect x="9" y="3" width="6" height="11" rx="3" /><path d="M5 11a7 7 0 0 0 14 0M12 18v3" /></>,
  hangup: <><path d="M3 15.5c5.3-4.7 12.7-4.7 18 0l-2.5 2.6-3-1.6v-2.4a11 11 0 0 0-7 0v2.4l-3 1.6L3 15.5z" /></>,
  send: <path d="M4 12l16-8-6 16-3-7-7-1z" />,
  volume: <><path d="M4 9h4l5-4v14l-5-4H4z" /><path d="M16.5 9a4 4 0 0 1 0 6M19 6.5a7.5 7.5 0 0 1 0 11" /></>,
  replay: <><path d="M4 12a8 8 0 1 0 2.4-5.7" /><path d="M4 4.5V9h4.5" /></>,
  info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v5.5M12 7.8v.1" /></>,
  user: <><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></>,
  map: <><path d="M9 4L3 6.5v13L9 17l6 3 6-2.5v-13L15 7 9 4z" /><path d="M9 4v13M15 7v13" /></>,
}

export default function Icon({ name, size = 20, label, className = '' }) {
  const path = PATHS[name]
  if (!path) return null
  return (
    <svg className={`icon ${className}`} width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
      role={label ? 'img' : undefined} aria-label={label} aria-hidden={label ? undefined : true} focusable="false">
      {path}
    </svg>
  )
}
