// Every call returns { ok, data, demo, error, message } and never throws.
// If the server cannot be reached (network error, 5xx, or an HTML page instead of JSON) and the call has
// a demo file, the demo JSON is returned with demo: true so no page is ever blank (section 8-H).

const DEMO = {
  analyze: 'analyze_kyc.json',
  pulse: 'pulse_alerts.json',
  news: 'news.json',
  services: 'services.json',
}

const OFFLINE = {
  ok: false,
  error: 'offline',
  message: 'Kavach cannot be reached right now. Check your connection and try again.',
}

async function demoFallback(name) {
  if (!name) return OFFLINE
  try {
    const res = await fetch(`/demo/${DEMO[name]}`)
    if (!res.ok) return OFFLINE
    return { ok: true, data: await res.json(), demo: true }
  } catch {
    return OFFLINE
  }
}

export async function call(path, { method = 'GET', body, form, demo } = {}) {
  let res
  try {
    res = await fetch(path, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: form ?? (body ? JSON.stringify(body) : undefined),
    })
  } catch {
    return demoFallback(demo)
  }
  const isJson = (res.headers.get('content-type') || '').includes('json')
  // 404/405: the route is not deployed yet (e.g. a teammate's endpoint), so treat it like the server being down
  if (res.status >= 500 || res.status === 404 || res.status === 405 || !isJson) return demoFallback(demo)
  let data = null
  try {
    data = await res.json()
  } catch {
    return demoFallback(demo)
  }
  if (res.ok) return { ok: true, data, demo: false }
  // 4xx: the server answered, so show its own plain-language message
  return { ok: false, error: data?.error || 'error', message: data?.message || 'That did not work. Please try again.' }
}

export const analyzeText = (text, language) =>
  call('/api/analyze', { method: 'POST', body: { text, language }, demo: 'analyze' })

export function analyzeFile(file, text, language) {
  const form = new FormData()
  form.append('file', file)
  if (text) form.append('text', text)
  form.append('language', language)
  return call('/api/analyze', { method: 'POST', form, demo: 'analyze' })
}

export const simStart = (language) => call('/api/sim/start', { method: 'POST', body: { language } })
export const simTurn = (session_id, user_message) =>
  call('/api/sim/turn', { method: 'POST', body: { session_id, user_message } })
export const simQuiz = (session_id, phase, answers) =>
  call('/api/sim/quiz', { method: 'POST', body: { session_id, phase, answers } })

export const pulseAlerts = () => call('/api/pulse/alerts', { demo: 'pulse' })
export const pulseReplay = () => call('/api/pulse/replay', { method: 'POST' })
export const getNews = () => call('/api/news', { demo: 'news' })
export const getServices = () => call('/api/services', { demo: 'services' })

// Links come from the server or demo files and are rendered as hrefs: plain web links only.
export const safeHref = (url) => (typeof url === 'string' && /^https?:\/\//i.test(url) ? url : undefined)
