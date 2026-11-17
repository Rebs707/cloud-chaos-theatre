import { describe, expect, it } from 'vitest'
import { getEventColor } from './eventColors'

describe('getEventColor', () => {
  it('returns red for fault_injected', () => {
    expect(getEventColor('fault_injected')).toBe('#ef5350')
  })

  it('returns green for fault_cleared', () => {
    expect(getEventColor('fault_cleared')).toBe('#36c98f')
  })

  it('returns amber for recovery_started', () => {
    expect(getEventColor('recovery_started')).toBe('#f5ad42')
  })

  it('returns green for recovery_completed', () => {
    expect(getEventColor('recovery_completed')).toBe('#36c98f')
  })

  it('returns cyan for service_state_change', () => {
    expect(getEventColor('service_state_change')).toBe('#43c8e8')
  })

  it('returns cyan for an unknown event kind', () => {
    expect(getEventColor('something_else')).toBe('#43c8e8')
  })

  it('returns cyan for inherited object property names', () => {
    expect(getEventColor('constructor')).toBe('#43c8e8')
  })
})
