const RED = '#ef5350'
const GREEN = '#36c98f'
const AMBER = '#f5ad42'
const CYAN = '#43c8e8'

export const DEFAULT_EVENT_COLOR = CYAN

// Keys match the backend EvidenceKind values exactly.
export const EVENT_KIND_COLORS: Readonly<Record<string, string>> = {
  fault_injected: RED,
  fault_cleared: GREEN,
  recovery_started: AMBER,
  recovery_completed: GREEN,
  service_state_change: CYAN,
}

export function getEventColor(kind: string): string {
  return Object.prototype.hasOwnProperty.call(EVENT_KIND_COLORS, kind)
    ? EVENT_KIND_COLORS[kind]
    : DEFAULT_EVENT_COLOR
}
