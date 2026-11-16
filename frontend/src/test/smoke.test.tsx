import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

function SmokeTest() {
  return <h1>Cloud Chaos Theatre</h1>
}

describe('Frontend setup', () => {
  it('renders the application title', () => {
    render(<SmokeTest />)
    expect(screen.getByText('Cloud Chaos Theatre')).toBeInTheDocument()
  })
})