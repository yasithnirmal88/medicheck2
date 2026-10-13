import React from 'react'
import AccessibleDialog from './AccessibleDialog'

const Drawer: React.FC<{
  open: boolean
  onClose: () => void
  ariaLabel?: string
  children?: React.ReactNode
}> = ({ open, onClose, ariaLabel = 'Navigation drawer', children }) => (
  <AccessibleDialog
    open={open}
    onClose={onClose}
    ariaLabel={ariaLabel}
    containerClassName="flex justify-end"
    panelClassName="h-full w-80 overflow-y-auto bg-white p-4 shadow-xl dark:bg-slate-800"
  >
    {children}
  </AccessibleDialog>
)

export default React.memo(Drawer)
