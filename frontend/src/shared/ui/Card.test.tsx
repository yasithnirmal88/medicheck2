import { render, screen } from '@testing-library/react'
import Card from './Card'

describe('Card', () => {
  it('renders children', () => {
    render(<Card>Hello</Card>)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('applies default Card classes', () => {
    render(<Card>Content</Card>)
    const div = screen.getByText('Content')
    expect(div.className).toContain('rounded')
    expect(div.className).toContain('shadow-sm')
    expect(div.className).toContain('bg-white')
  })

  it('applies additional className', () => {
    render(<Card className="extra-class">Content</Card>)
    expect(screen.getByText('Content').className).toContain('extra-class')
  })
})
