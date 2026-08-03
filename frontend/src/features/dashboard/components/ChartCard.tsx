import React from 'react'
import Card from './Card'

interface ChartCardProps {
  title: string
  subtitle?: string
  action?: React.ReactNode
  children: React.ReactNode
}

const ChartCard: React.FC<ChartCardProps> = ({ title, subtitle, action, children }) => {
  return (
    <Card className="flex h-full flex-col">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">{title}</h3>
          {subtitle ? <p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">{subtitle}</p> : null}
        </div>
        {action}
      </div>
      <div className="mt-4 flex flex-1 items-center h-64">{children}</div>
    </Card>
  )
}

export default React.memo(ChartCard)