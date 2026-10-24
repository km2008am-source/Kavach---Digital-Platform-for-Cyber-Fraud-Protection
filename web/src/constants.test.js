import { describe, it, expect } from 'vitest'
import { alertRadius, districtPos, normalizeService, riskTone } from './constants.js'

describe('constants', () => {
  it('maps risk to tone', () => {
    expect(riskTone('high')).toBe('red'); expect(riskTone('low')).toBe('green'); expect(riskTone('x')).toBe('amber')
  })
  it('keeps marker radius bounded and growing', () => {
    expect(alertRadius(0)).toBe(12)
    expect(alertRadius(38)).toBeGreaterThan(alertRadius(5))
    expect(alertRadius(1e6)).toBe(60)
  })
  it('knows Coimbatore and returns null for unknown districts', () => {
    expect(districtPos('Coimbatore')).toHaveLength(2)
    expect(districtPos('Atlantis')).toBeNull()
  })
  it("maps Person 1's /api/services shape onto the page's fields", () => {
    const s = normalizeService({ name: '1930', situation: 'I lost money to an online scam',
      description: 'Call 1930 now.', official_url: 'https://cybercrime.gov.in/' })
    expect(s.situation).toBe('lost_money')
    expect(s.what).toBe('Call 1930 now.')
    expect(s.link).toBe('https://cybercrime.gov.in/')
    expect(normalizeService({ situation: 'My phone was lost or stolen' }).situation).toBe('lost_phone')
    expect(normalizeService({ situation: 'I found a suspicious deposit or investment scheme' }).situation).toBe('investment')
    expect(normalizeService({ situation: 'suspicious', what: 'x', link: 'https://a.in' }).situation).toBe('suspicious')
    expect(normalizeService(null)).toBeNull()
  })
})
