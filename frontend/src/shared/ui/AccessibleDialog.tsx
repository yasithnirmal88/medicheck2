import React, { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'

interface AccessibleDialogProps {
  open: boolean
  onClose: () => void
  ariaLabel: string
  containerClassName?: string
  backdropClassName?: string
  panelClassName?: string
  children: React.ReactNode
}

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

const AccessibleDialog: React.FC<AccessibleDialogProps> = ({
  open,
  onClose,
  ariaLabel,
  containerClassName = '',
  backdropClassName = '',
  panelClassName = '',
  children,
}) => {
  const panelRef = useRef<HTMLDivElement>(null)
  const onCloseRef = useRef(onClose)

  useEffect(() => {
    onCloseRef.current = onClose
  }, [onClose])

  useEffect(() => {
    if (!open) return

    const panel = panelRef.current
    if (!panel) return

    const previouslyFocused = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    const getFocusableElements = () =>
      Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)).filter(
        (element) =>
          !element.hidden &&
          element.getAttribute('aria-hidden') !== 'true' &&
          window.getComputedStyle(element).display !== 'none' &&
          window.getComputedStyle(element).visibility !== 'hidden',
      )

    const initialFocus = panel.querySelector<HTMLElement>('[autofocus]')
      ?? getFocusableElements()[0]
      ?? panel
    initialFocus.focus()

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        onCloseRef.current()
        return
      }

      if (event.key !== 'Tab') return
      const focusableElements = getFocusableElements()
      if (focusableElements.length === 0) {
        event.preventDefault()
        panel.focus()
        return
      }

      const first = focusableElements[0]
      const last = focusableElements[focusableElements.length - 1]
      const active = document.activeElement

      if (event.shiftKey && (active === first || !panel.contains(active))) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && (active === last || !panel.contains(active))) {
        event.preventDefault()
        first.focus()
      }
    }

    const handleFocusIn = (event: FocusEvent) => {
      if (event.target instanceof Node && !panel.contains(event.target)) {
        const target = getFocusableElements()[0] ?? panel
        target.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('focusin', handleFocusIn)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('focusin', handleFocusIn)
      document.body.style.overflow = previousOverflow
      if (previouslyFocused?.isConnected) previouslyFocused.focus()
    }
  }, [open])

  if (!open) return null

  return createPortal(
    <div className={`fixed inset-0 z-50 ${containerClassName}`}>
      <div
        aria-hidden="true"
        className={`absolute inset-0 bg-black/50 ${backdropClassName}`}
        onClick={onClose}
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={ariaLabel}
        tabIndex={-1}
        className={`relative ${panelClassName}`}
      >
        {children}
      </div>
    </div>,
    document.body,
  )
}

export default React.memo(AccessibleDialog)
