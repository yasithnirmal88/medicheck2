import React, { useId } from 'react'
import { Area, AreaChart, ResponsiveContainer, YAxis } from 'recharts'

type Tone = 'primary' | 'accent' | 'success' | 'warning' | 'danger'

const strokeByTone: Record<Tone, string> = {
  primary: '#2563EB',
  accent: '#14B8A6',
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
}

interface SparklineProps {
  data: number[]
  tone?: Tone
  className?: string
}

export const Sparkline: React.FC<SparklineProps> = ({ data, tone = 'primary', className }) => {
  const id = useId()
  const points = data.map((value, index) => ({ x: index, y: value }))
  const gradientId = `spark-${id}`

  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={points} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={strokeByTone[tone]} stopOpacity={0.22} />
              <stop offset="100%" stopColor={strokeByTone[tone]} stopOpacity={0} />
            </linearGradient>
          </defs>
          <YAxis hide domain={['dataMin - 5', 'dataMax + 5']} />
          <Area
            type="monotone"
            dataKey="y"
            stroke={strokeByTone[tone]}
            strokeWidth={2}
            fill={`url(#${gradientId})`}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}