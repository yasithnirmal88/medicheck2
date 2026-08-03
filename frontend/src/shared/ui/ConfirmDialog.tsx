import React from 'react'
import Modal from './Modal'
import Button from './Button'

const ConfirmDialog: React.FC<{
  open: boolean
  title?: string
  message?: string
  onCancel: () => void
  onConfirm: () => void
}> = ({ open, title = 'Confirm', message, onCancel, onConfirm }) => {
  return (
    <Modal open={open} onClose={onCancel} title={title}>
      <p className="mb-4">{message}</p>
      <div className="flex justify-end gap-2">
        <Button variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
        <Button variant="danger" onClick={onConfirm}>
          Confirm
        </Button>
      </div>
    </Modal>
  )
}

export default React.memo(ConfirmDialog)
