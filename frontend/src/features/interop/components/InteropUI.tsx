/**
 * Phase 10 — shared presentational components for the interoperability area.
 */
import React from 'react'

export const SuppressedBadge: React.FC = () => (
  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
    Suppressed
  </span>
)

export const PrivacyBadge: React.FC<{ threshold?: number }> = ({ threshold = 10 }) => (
  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
    k-anonymity ≥ {threshold}
  </span>
)

export const SectionCard: React.FC<{
  title: string
  disclaimer?: string
  badge?: React.ReactNode
  children: React.ReactNode
}> = ({ title, disclaimer, badge, children }) => (
  <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5">
    <div className="flex items-center justify-between gap-2">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{title}</h3>
      {badge}
    </div>
    {disclaimer && (
      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 italic">{disclaimer}</p>
    )}
    <div className="mt-4">{children}</div>
  </div>
)

export const TransparencyNotice: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => (
  <div className="rounded-lg border border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-900/20 p-4">
    <p className="text-sm text-blue-800 dark:text-blue-300">{children}</p>
  </div>
)

export const ErrorState: React.FC<{ message: string }> = ({ message }) => (
  <div className="rounded-lg border border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-900/20 p-4">
    <p className="text-sm text-red-700 dark:text-red-400">{message}</p>
  </div>
)

export const LoadingState: React.FC = () => (
  <div className="flex items-center justify-center py-8">
    <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
  </div>
)

export const EmptyState: React.FC<{ message: string }> = ({ message }) => (
  <div className="flex flex-col items-center justify-center py-8 text-center">
    <p className="text-sm text-slate-500 dark:text-slate-400">{message}</p>
  </div>
)

export const MetricCard: React.FC<{
  label: string
  value: number | null
  suppressed?: boolean
  suffix?: string
}> = ({ label, value, suppressed, suffix }) => (
  <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-4">
    <div className="flex items-center justify-between">
      <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
        {suppressed ? '—' : value == null ? '—' : value.toLocaleString()}
        {suffix && !suppressed && value != null ? suffix : ''}
      </p>
      {suppressed && <SuppressedBadge />}
    </div>
    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{label}</p>
  </div>
)
