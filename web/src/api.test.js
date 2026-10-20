import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { call, safeHref } from './api.js'

const json = (body, status = 200, type = 'application/json') =>
  new Response(typeof body === 'string' ? body : JSON.stringify(body), { status, headers: { 'content-type': type } })

let fetchMock
beforeEach(() => { fetchMock = vi.fn(); vi.stubGlobal('fetch', fetchMock) })
afterEach(() => vi.unstubAllGlobals())

describe('call', () => {
  it('returns server data on success', async () => {
    fetchMock.mockResolvedValueOnce(json({ a: 1 }))
    expect(await call('/api/x', { demo: 'news' })).toEqual({ ok: true, data: { a: 1 }, demo: false })
  })

  it('passes a 4xx message through instead of using demo data', async () => {
    fetchMock.mockResolvedValueOnce(json({ error: 'empty_input', message: 'Paste a message.' }, 422))
    const r = await call('/api/analyze', { demo: 'analyze' })
    expect(r).toEqual({ ok: false, error: 'empty_input', message: 'Paste a message.' })
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('uses demo JSON when the network fails', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('failed')).mockResolvedValueOnce(json([{ id: 1 }]))
    const r = await call('/api/news', { demo: 'news' })
    expect(r).toEqual({ ok: true, data: [{ id: 1 }], demo: true })
    expect(fetchMock.mock.calls[1][0]).toBe('/demo/news.json')
  })

  it('uses demo JSON on a 5xx', async () => {
    fetchMock.mockResolvedValueOnce(json({ error: 'server_error' }, 500)).mockResolvedValueOnce(json({ ok: 1 }))
    expect((await call('/api/pulse/alerts', { demo: 'pulse' })).demo).toBe(true)
  })

  it('uses demo JSON when the route is not deployed (404)', async () => {
    fetchMock.mockResolvedValueOnce(json({ error: 'not_found' }, 404)).mockResolvedValueOnce(json([{ id: 'x' }]))
    const r = await call('/api/services', { demo: 'services' })
    expect(r).toEqual({ ok: true, data: [{ id: 'x' }], demo: true })
  })

  it('treats an HTML page as the server being down', async () => {
    fetchMock.mockResolvedValueOnce(json('<html></html>', 200, 'text/html')).mockResolvedValueOnce(json([]))
    expect((await call('/api/news', { demo: 'news' })).demo).toBe(true)
  })

  it('treats invalid JSON as the server being down', async () => {
    fetchMock.mockResolvedValueOnce(json('{not json', 200)).mockResolvedValueOnce(json([]))
    expect((await call('/api/news', { demo: 'news' })).demo).toBe(true)
  })

  it('reports offline when there is no demo file for the call', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('failed'))
    const r = await call('/api/sim/start', { method: 'POST', body: {} })
    expect(r.ok).toBe(false)
    expect(r.error).toBe('offline')
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('reports offline when the demo file is also missing', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('failed')).mockResolvedValueOnce(json({}, 404))
    expect((await call('/api/news', { demo: 'news' })).error).toBe('offline')
  })

  it('sends JSON bodies with a content type', async () => {
    fetchMock.mockResolvedValueOnce(json({}))
    await call('/api/sim/turn', { method: 'POST', body: { a: 1 } })
    const [, init] = fetchMock.mock.calls[0]
    expect(init.method).toBe('POST')
    expect(init.headers['Content-Type']).toBe('application/json')
    expect(init.body).toBe('{"a":1}')
  })
})

describe('safeHref', () => {
  it('allows only http(s) links', () => {
    expect(safeHref('https://example.com/a')).toBe('https://example.com/a')
    expect(safeHref('http://example.com')).toBe('http://example.com')
    for (const bad of ['javascript:alert(1)', 'data:text/html,x', '//evil.com', '', null, undefined, 5]) {
      expect(safeHref(bad)).toBeUndefined()
    }
  })
})
