import React from 'react'
import { TrendingUp } from 'lucide-react'
import { Area, AreaChart, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import ChartCard from './ChartCard'
import EmptyState from './EmptyState'

export interface ChartPoint {
  label: string
  value: number
}

export interface WeightPoint {
  label: string
  weight: number
  bmi: number
}

interface HealthChartsProps {
  scoreSeries: ChartPoint[]
  weightSeries: WeightPoint[]
  loading?: boolean
}

const tooltipStyle: React.CSSProperties = {
  borderRadius: 12,
  border: '1px solid #e2e8f0',
  fontSize: 12,
}

export const HealthCharts: React.FC<HealthChartsProps> = ({ scoreSeries, weightSeries, loading }) => {
  const hasScore = scoreSeries.length > 0
  const hasWeight = weightSeries.length > 0

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <ChartCard title="Health Score over time" subtitle="Risk-adjusted wellbeing trend">
        {loading ? (
          <ChartSkeleton />
        ) : hasScore ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={scoreSeries} margin={{ top: 5, right: 8, left: -18, bottom: 0 }}>
              <defs>
                <linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#2563EB" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#2563EB" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="label" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area type="monotone" dataKey="value" stroke="#2563EB" strokeWidth={2} fill="url(#scoreFill)" />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <EmptyState icon={TrendingUp} title="No score history yet" description="Complete assessments to track your health score." />
        )}
      </ChartCard>

      <ChartCard title="Weight & BMI trend" subtitle="Anthropometric measurements">
        {loading ? (
          <ChartSkeleton />
        ) : hasWeight ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={weightSeries} margin={{ top: 5, right: 8, left: -20, bottom: 0 }}>
              <XAxis dataKey="label" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={tooltipStyle} />
              <Line type="monotone" dataKey="weight" name="Weight" stroke="#14B8A6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="bmi" name="BMI" stroke="#8B5CF6" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <EmptyState icon={TrendingUp} title="No measurements recorded" description="Log your weight to see BMI trends." />
        )}
      </ChartCard>
    </div>
  )
}

function ChartSkeleton() {
  return <div className="h-full w-full animate-pulse rounded-lg bg-slate-100 dark:bg-slate-700/50" />
}

export default HealthCharts