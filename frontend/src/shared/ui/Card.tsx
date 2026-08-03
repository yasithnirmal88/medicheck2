import React from 'react'

const Card: React.FC<React.PropsWithChildren<{ className?: string }>> = ({ children, className = '' }) => (
  <div className={`rounded shadow-sm bg-white dark:bg-slate-800 p-4 ${className}`}>{children}</div>
)

export default React.memo(Card)
