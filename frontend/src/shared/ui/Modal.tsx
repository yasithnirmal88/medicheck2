import React from 'react'
import { createPortal } from 'react-dom'

type ModalProps = {
  open: boolean
  onClose: () => void
  title?: string
  children?: React.ReactNode
}

const Modal: React.FC<ModalProps> = React.memo(({ open, onClose, title, children }) => {
  if (!open) return null
  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black opacity-30" onClick={onClose} />
      <div className="relative bg-white dark:bg-slate-800 rounded shadow p-6 w-full max-w-xl">
        {title && <h3 className="text-lg mb-4">{title}</h3>}
        {children}
      </div>
    </div>,
    document.body,
  )
}) as React.FC<ModalProps>

Modal.displayName = 'Modal'
export default Modal
