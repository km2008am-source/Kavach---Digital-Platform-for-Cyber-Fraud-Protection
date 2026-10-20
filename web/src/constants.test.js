import { describe, it, expect } from 'vitest'
import { alertRadius, districtPos, riskTone } from './constants.js'

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
})
