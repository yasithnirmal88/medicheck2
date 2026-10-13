/**
 * Phase 10 — Interoperability dashboard page.
 *
 * Admin/clinician view for:
 *  - FHIR bundle export (consent-aware, audited, read-only)
 *  - Export history (audit trail of past exports)
 *  - Transparency notices
 *
 * Patients do not see this page. Exports are RBAC + consent gated on the
 * backend; this UI only triggers already-authorized endpoints.
 */
import React, { useState } from 'react'
import { FileJson, History, ShieldCheck, Download } from 'lucide-react'
import {
  useFhirPatientBundle,
  useExportHistory,
} from '../hooks/useInteropQueries'
import {
  SectionCard,
  TransparencyNotice,
  ErrorState,
  LoadingState,
  EmptyState,
} from '../components/InteropUI'

const ResourceTypeBadge: React.FC<{ type: string }> = ({ type }) => (
  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400">
    {type}
  </span>
)

const ExportRow: React.FC<{
  id: string
  patientId: string | null
  status: string
  types: string[]
  createdAt: string
  itemCount: number
}> = ({ id, patientId, status, types, createdAt, itemCount }) => (
  <tr className="border-t border-slate-100 dark:border-slate-800">
    <td className="py-2 px-3 text-xs font-mono text-slate-600 dark:text-slate-400 truncate max-w-[120px]">
      {id.slice(0, 12)}…
    </td>
    <td className="py-2 px-3 text-xs text-slate-600 dark:text-slate-400">
      {patientId ? patientId.slice(0, 8) + '…' : '—'}
    </td>
    <td className="py-2 px-3">
      <span
        className={`text-xs font-medium ${
          status === 'completed'
            ? 'text-emerald-600 dark:text-emerald-400'
            : 'text-amber-600 dark:text-amber-400'
        }`}
      >
        {status}
      </span>
    </td>
    <td className="py-2 px-3">
      <div className="flex flex-wrap gap-1">
        {types.slice(0, 4).map((t) => (
          <ResourceTypeBadge key={t} type={t} />
        ))}
        {types.length > 4 && (
          <span className="text-xs text-slate-400">+{types.length - 4}</span>
        )}
      </div>
    </td>
    <td className="py-2 px-3 text-xs text-slate-600 dark:text-slate-400">
      {itemCount}
    </td>
    <td className="py-2 px-3 text-xs text-slate-500 dark:text-slate-400">
      {new Date(createdAt).toLocaleString()}
    </td>
  </tr>
)

export const InteroperabilityDashboardPage: React.FC = () => {
  const [patientId, setPatientId] = useState('')
  const [activePatientId, setActivePatientId] = useState<string | null>(null)

  const bundle = useFhirPatientBundle(activePatientId)
  const history = useExportHistory()

  const handleExport = () => {
    const trimmed = patientId.trim()
    if (trimmed) setActivePatientId(trimmed)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          Interoperability
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          FHIR R4 export, export history, and health-system integration.
        </p>
      </div>

      <TransparencyNotice>
        This export contains structured health information intended for
        authorized healthcare interoperability. Exports are consent-aware,
        RBAC-controlled, and audited. AI assistance does not determine clinical
        risk or diagnosis.
      </TransparencyNotice>

      <SectionCard
        title="FHIR Bundle Export"
        disclaimer="Generate a FHIR R4 Bundle (Patient, QuestionnaireResponse, Observation, DiagnosticReport, ServiceRequest, Task) from deterministic MediCheck data."
      >
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Patient ID"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            className="flex-1 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm text-slate-900 dark:text-white"
            aria-label="Patient ID"
          />
          <button
            type="button"
            onClick={handleExport}
            disabled={!patientId.trim() || bundle.isLoading}
            className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 hover:bg-indigo-700"
          >
            <Download className="h-4 w-4" />
            {bundle.isLoading ? 'Generating…' : 'Export FHIR'}
          </button>
        </div>

        {bundle.isError && (
          <div className="mt-4">
            <ErrorState message="Export denied. The patient may not have granted consent, or you lack authorization for this patient." />
          </div>
        )}

        {bundle.data && (
          <div className="mt-4 space-y-3">
            <div className="flex items-center gap-2 text-sm">
              <FileJson className="h-4 w-4 text-indigo-500" />
              <span className="font-medium text-slate-900 dark:text-white">
                Bundle {bundle.data.bundle.id.slice(0, 12)}…
              </span>
              <span className="text-slate-400">·</span>
              <span className="text-slate-500 dark:text-slate-400">
                {bundle.data.manifest.item_count} resources
              </span>
              <span className="text-slate-400">·</span>
              <span className="text-slate-500 dark:text-slate-400">
                FHIR {bundle.data.manifest.schema_version}
              </span>
            </div>
            <div className="flex flex-wrap gap-1">
              {bundle.data.manifest.resource_types.map((t) => (
                <ResourceTypeBadge key={t} type={t} />
              ))}
            </div>
            <details className="rounded-md border border-slate-200 dark:border-slate-700">
              <summary className="cursor-pointer px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300">
                View JSON Bundle
              </summary>
              <pre className="max-h-96 overflow-auto bg-slate-50 dark:bg-slate-800 p-3 text-xs text-slate-700 dark:text-slate-300">
                {JSON.stringify(bundle.data.bundle, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </SectionCard>

      <SectionCard
        title="Export History"
        badge={
          <span className="inline-flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
            <ShieldCheck className="h-3.5 w-3.5" />
            Audited
          </span>
        }
      >
        {history.isPending && <LoadingState />}
        {history.isError && (
          <ErrorState message="Could not load export history." />
        )}
        {history.data && history.data.items.length === 0 && (
          <EmptyState message="No exports recorded yet." />
        )}
        {history.data && history.data.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-xs uppercase text-slate-400">
                  <th className="py-2 px-3">Export ID</th>
                  <th className="py-2 px-3">Patient</th>
                  <th className="py-2 px-3">Status</th>
                  <th className="py-2 px-3">Resources</th>
                  <th className="py-2 px-3">Items</th>
                  <th className="py-2 px-3">Created</th>
                </tr>
              </thead>
              <tbody>
                {history.data.items.map((item) => (
                  <ExportRow
                    key={item.id}
                    id={item.id}
                    patientId={item.patient_user_id}
                    status={item.status}
                    types={item.resource_types}
                    createdAt={item.created_at}
                    itemCount={item.item_count}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
        {history.data && (
          <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
            <History className="h-3.5 w-3.5" />
            {history.data.total} export(s) on record. Audit metadata only — no
            bundle payloads are stored.
          </div>
        )}
      </SectionCard>
    </div>
  )
}

export default InteroperabilityDashboardPage
