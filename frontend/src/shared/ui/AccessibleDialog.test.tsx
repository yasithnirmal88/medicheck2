import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import AccessibleDialog from './AccessibleDialog'

function DialogHarness() {
  const [open, setOpen] = useState(false)

  return (
    <>
      <button type="button" onClick={() => setOpen(true)}>Return focus</button>
      <AccessibleDialog
        open={open}
        onClose={() => setOpen(false)}
        ariaLabel="Example dialog"
      >
        <button type="button">First action</button>
        <button type="button">Last action</button>
      </AccessibleDialog>
    </>
  )
}

describe('AccessibleDialog', () => {
  it('announces dialog semantics and traps keyboard focus', async () => {
    const user = userEvent.setup()
    render(<DialogHarness />)
    await user.click(screen.getByRole('button', { name: 'Return focus' }))

    const dialog = screen.getByRole('dialog', { name: 'Example dialog' })
    const firstAction = screen.getByRole('button', { name: 'First action' })
    const lastAction = screen.getByRole('button', { name: 'Last action' })

    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(firstAction).toHaveFocus()

    await user.tab({ shift: true })
    expect(lastAction).toHaveFocus()

    await user.tab()
    expect(firstAction).toHaveFocus()
  })

  it('closes with Escape and restores focus to the opener', async () => {
    const user = userEvent.setup()
    render(<DialogHarness />)

    await user.click(screen.getByRole('button', { name: 'Return focus' }))
    expect(screen.getByRole('dialog', { name: 'Example dialog' })).toBeInTheDocument()

    fireEvent.keyDown(document, { key: 'Escape' })

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Return focus' })).toHaveFocus()
  })
})
