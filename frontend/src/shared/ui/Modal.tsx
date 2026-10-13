import React from 'react'
import AccessibleDialog from './AccessibleDialog'

type ModalProps = {
  open: boolean
  onClose: () => void
  title?: string
  children?: React.ReactNode
}

const Modal: React.FC<ModalProps> = React.memo(({ open, onClose, title, children }) => {
  return (
    <AccessibleDialog
      open={open}
      onClose={onClose}
      ariaLabel={title ?? 'Dialog'}
      containerClassName="flex items-center justify-center"
      backdropClassName="bg-black/30"
      panelClassName="bg-white dark:bg-slate-800 rounded shadow p-6 w-full max-w-xl"
    >
      <>
        {title && <h2 className="text-lg mb-4">{title}</h2>}
        {children}
      </>
    </AccessibleDialog>
  )
}) as React.FC<ModalProps>

Modal.displayName = 'Modal'
export default Modal
