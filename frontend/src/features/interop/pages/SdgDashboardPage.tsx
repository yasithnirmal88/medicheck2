/**
 * Phase 10 — SDG / population-health export dashboard.
 *
 * Renders de-identified, k-anonymity-suppressed SDG-aligned metrics
 * (SDG 3.4, 3.8, 10). Supports JSON view + CSV download. Every metric
 * documents its methodology + limitations and distinguishes official SDG
 * indicators from MediCheck-aligned proxies.
 */
import React, { useState } from 'react'
import { Download, Globe2, FileSpreadsheet } from 'lucide-react'
import { useSdgExport, useSdgCsv } from '../hooks/useInteropQueries'
import {
  SectionCard,
  TransparencyNotice,
  PrivacyBadge,
  ErrorState,
  LoadingState,
  EmptyState,
} from '../components/InteropUI'

const SdgTargetLabel: React.FC<{ target: string }> = ({ target }) => {
  const colors: Record<string, string> = {
    'sdg-3-4': 'bg-rose-50 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400',
    'sdg-3-8': 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    'sdg-10': 'bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  }
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
        colors[target] ?? 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
      }`}
    >
      {target.toUpperCase()}
    </span>
  )
}

const SdgRow: React.FC<{
  indicator: string
  target: string
  type: string
  value: number | null
  numerator: number | null
  denominator: number | null
  suppression: string
  methodology: string
  limitations: string
  period: string
}> = ({
  indicator,
  target,
  type,
  value,
  numerator,
  denominator,
  suppression,
  methodology,
  limitations,
  period,
}) => {
  const suppressed = suppression !== 'none' && suppression !== 'ok'
  return (
    <div className="border-t border-slate-100 dark:border-slate-800 py-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <SdgTargetLabel target={target} />
            <span className="text-sm font-medium text-slate-900 dark:text-white">
              {indicator}
            </span>
            {type === 'medicheck-aligned-proxy' && (
              <span className="text-xs text-amber-600 dark:text-amber-400">
                (proxy)
              </span>
            )}
          </div>
          <p className="mt-0.5 text-xs text-slate-400">
            Period: {period}
            {numerator != null && ` · Numerator: ${numerator}`}
            {denominator != null && ` · Denominator: ${denominator}`}
          </p>
        </div>
        <div className="text-right">
          {suppressed ? (
            <span className="text-xs text-slate-400">Suppressed</span>
          ) : (
            <span className="text-xl font-bold text-slate-900 dark:text-white">
              {value == null ? '—' : value.toLocaleString()}
            </span>
          )}
        </div>
      </div>
      <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
        <span className="font-medium">Methodology:</span> {methodology}
      </p>
      <p className="mt-1 text-xs text-slate-400">
        <span className="font-medium">Limitations:</span> {limitations}
      </p>
    </div>
  )
}

export const SdgDashboardPage: React.FC = () => {
  const [downloadCsv, setDownloadCsv] = useState(false)
  const sdg = useSdgExport()
  const csv = useSdgCsv(undefined, downloadCsv)

  const handleDownload = () => {
    setDownloadCsv(true)
  }

  React.useEffect(() => {
    if (csv.isSuccess && csv.data) {
      const blob = new Blob([csv.data], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `medicheck-sdg-export-${new Date().toISOString().slice(0, 10)}.csv`
      a.click()
      URL.revokeObjectURL(url)
      setDownloadCsv(false)
    }
  }, [csv.isSuccess, csv.data])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            SDG Analytics
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            De-identified, aggregated SDG-aligned population metrics.
          </p>
        </div>
        <button
          type="button"
          onClick={handleDownload}
          disabled={csv.isPending}
          className="inline-flex items-center gap-2 rounded-md border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
        >
          <Download className="h-4 w-4" />
          Download CSV
        </button>
      </div>

      <TransparencyNotice>
        This information is aggregated and de-identified for health-system and
        research purposes. Small cohorts (below the k-anonymity threshold) are
        suppressed. MediCheck-aligned proxies are NOT official UN SDG indicators
        unless explicitly labelled.
      </TransparencyNotice>

      {sdg.isPending && <LoadingState />}
      {sdg.isError && (
        <ErrorState message="Could not load SDG analytics. You may lack the required research/admin role." />
      )}
      {sdg.data && (
        <>
          <div className="flex items-center gap-2">
            <PrivacyBadge threshold={sdg.data.privacy_threshold} />
            <span className="inline-flex items-center gap-1 text-xs text-slate-400">
              <Globe2 className="h-3.5 w-3.5" />
              Generated {new Date(sdg.data.generated_at).toLocaleString()}
            </span>
          </div>

          <SectionCard
            title="SDG Indicators"
            badge={
              <span className="inline-flex items-center gap-1 text-xs text-slate-400">
                <FileSpreadsheet className="h-3.5 w-3.5" />
                {sdg.data.rows.length} metric(s)
              </span>
            }
          >
            {sdg.data.rows.length === 0 ? (
              <EmptyState message="No SDG metrics available for the selected period." />
            ) : (
              sdg.data.rows.map((row, i) => (
                <SdgRow
                  key={`${row.indicator}-${i}`}
                  indicator={row.indicator}
                  target={row.sdg_target}
                  type={row.indicator_type}
                  value={row.value}
                  numerator={row.numerator}
                  denominator={row.denominator}
                  suppression={row.suppression_status}
                  methodology={row.methodology}
                  limitations={row.limitations}
                  period={row.period}
                />
              ))
            )}
          </SectionCard>
        </>
      )}
    </div>
  )
}

export default SdgDashboardPage
