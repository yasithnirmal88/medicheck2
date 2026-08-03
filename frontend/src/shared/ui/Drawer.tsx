import React from 'react'
import { createPortal } from 'react-dom'

const Drawer: React.FC<{
  open: boolean
  onClose: () => void
  children?: React.ReactNode
}> = ({ open, onClose, children }) => {
  if (!open) return null
  return createPortal(
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1" onClick={onClose} />
      <div className="w-80 bg-white dark:bg-slate-800 p-4 shadow-xl">{children}</div>
    </div>,
    document.body,
  )
}

export default React.memo(Drawer)
