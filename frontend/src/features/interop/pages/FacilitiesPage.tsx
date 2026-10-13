/**
 * Phase 10 — Facility registry + referral status admin page.
 *
 * Lists seeded/demo facilities and active referrals with their deterministic
 * lifecycle status + receiving-side facility feedback. Admin/interop role
 * only. Patients do not see this page.
 */
import React, { useState } from 'react'
import { Building2, Plus, Send } from 'lucide-react'
import {
  useFacilities,
  useCreateFacility,
  useReferrals,
  useRecordFacilityFeedback,
} from '../hooks/useInteropQueries'
import {
  SectionCard,
  TransparencyNotice,
  ErrorState,
  LoadingState,
  EmptyState,
} from '../components/InteropUI'
import type { ReceivingStatus, Referral } from '../api/interopService'

const StatusPill: React.FC<{ status: string }> = ({ status }) => {
  const tones: Record<string, string> = {
    completed: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
    cancelled: 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400',
    declined: 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    lost_to_followup: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    expired: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  }
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
        tones[status] ?? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
      }`}
    >
      {status.replace(/_/g, ' ')}
    </span>
  )
}

const FacilityCard: React.FC<{
  code: string
  name: string
  serviceType: string | null
  region: string | null
  availability: string
  services: { service_type: string | null; name: string | null }[]
}> = ({ code, name, serviceType, region, availability, services }) => (
  <div className="rounded-lg border border-slate-200 dark:border-slate-800 p-4">
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Building2 className="h-4 w-4 text-slate-400" />
        <span className="font-medium text-slate-900 dark:text-white">{name}</span>
      </div>
      <StatusPill status={availability} />
    </div>
    <p className="mt-1 text-xs text-slate-400">
      {code}
      {serviceType && ` · ${serviceType}`}
      {region && ` · ${region}`}
    </p>
    {services.length > 0 && (
      <div className="mt-2 flex flex-wrap gap-1">
        {services.map((s, i) => (
          <span
            key={i}
            className="text-xs px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
          >
            {s.name ?? s.service_type ?? 'service'}
          </span>
        ))}
      </div>
    )}
  </div>
)

const ReferralRow: React.FC<{
  referral: Referral
  onFeedback: (referralId: string, status: ReceivingStatus) => void
  pending: boolean
}> = ({ referral, onFeedback, pending }) => {
  const [status, setStatus] = useState<ReceivingStatus>(referral.receiving_status)
  const isTerminal = ['completed', 'cancelled', 'declined', 'lost_to_followup', 'expired'].includes(
    referral.status
  )
  return (
    <tr className="border-t border-slate-100 dark:border-slate-800">
      <td className="py-2 px-3 text-xs font-mono text-slate-600 dark:text-slate-400">
        {referral.id.slice(0, 10)}…
      </td>
      <td className="py-2 px-3 text-xs text-slate-600 dark:text-slate-400">
        {referral.referral_type.replace(/_/g, ' ')}
      </td>
      <td className="py-2 px-3">
        <StatusPill status={referral.status} />
      </td>
      <td className="py-2 px-3 text-xs text-slate-600 dark:text-slate-400">
        {referral.facility_name ?? referral.facility_id?.slice(0, 8) ?? '—'}
      </td>
      <td className="py-2 px-3 text-xs text-slate-600 dark:text-slate-400">
        {referral.scheduled_for
          ? new Date(referral.scheduled_for).toLocaleDateString()
          : '—'}
      </td>
      <td className="py-2 px-3">
        {isTerminal ? (
          <span className="text-xs text-slate-400">—</span>
        ) : (
          <div className="flex items-center gap-1">
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as ReceivingStatus)}
              className="text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-1.5 py-1 text-slate-700 dark:text-slate-300"
              aria-label="Receiving status"
            >
              <option value="pending">pending</option>
              <option value="received">received</option>
              <option value="accepted">accepted</option>
              <option value="declined">declined</option>
              <option value="completed">completed</option>
            </select>
            <button
              type="button"
              onClick={() => onFeedback(referral.id, status)}
              disabled={pending}
              className="inline-flex items-center gap-1 rounded bg-slate-600 px-2 py-1 text-xs text-white disabled:opacity-50 hover:bg-slate-700"
            >
              <Send className="h-3 w-3" />
              Update
            </button>
          </div>
        )}
      </td>
    </tr>
  )
}

export const FacilitiesPage: React.FC = () => {
  const facilities = useFacilities()
  const referrals = useReferrals()
  const createFacility = useCreateFacility()
  const feedback = useRecordFacilityFeedback()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    code: '',
    name: '',
    service_type: '',
    region: '',
  })

  const handleCreate = () => {
    if (!form.code || !form.name) return
    createFacility.mutate(
      {
        code: form.code,
        name: form.name,
        service_type: form.service_type || undefined,
        region: form.region || undefined,
      },
      {
        onSuccess: () => {
          setShowForm(false)
          setForm({ code: '', name: '', service_type: '', region: '' })
        },
      }
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Facilities & Referrals
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Facility registry and referral lifecycle management.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowForm((v) => !v)}
          className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" />
          Add Facility
        </button>
      </div>

      <TransparencyNotice>
        Referral status transitions are deterministic and auditable. Facility
        feedback is recorded by authorized receiving-side users or CHWs.
        Outcomes never alter clinical scores.
      </TransparencyNotice>

      {showForm && (
        <SectionCard title="New Facility">
          <div className="grid grid-cols-2 gap-3">
            <input
              placeholder="Code (unique)"
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })}
              className="rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm text-slate-900 dark:text-white"
            />
            <input
              placeholder="Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm text-slate-900 dark:text-white"
            />
            <input
              placeholder="Service type"
              value={form.service_type}
              onChange={(e) => setForm({ ...form, service_type: e.target.value })}
              className="rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm text-slate-900 dark:text-white"
            />
            <input
              placeholder="Region"
              value={form.region}
              onChange={(e) => setForm({ ...form, region: e.target.value })}
              className="rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm text-slate-900 dark:text-white"
            />
          </div>
          {createFacility.isError && (
            <p className="mt-2 text-sm text-red-600 dark:text-red-400">
              Could not create facility (duplicate code or insufficient permission).
            </p>
          )}
          <button
            type="button"
            onClick={handleCreate}
            disabled={createFacility.isPending}
            className="mt-3 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 hover:bg-emerald-700"
          >
            {createFacility.isPending ? 'Creating…' : 'Create'}
          </button>
        </SectionCard>
      )}

      <SectionCard title="Facility Registry">
        {facilities.isPending && <LoadingState />}
        {facilities.isError && (
          <ErrorState message="Could not load facilities." />
        )}
        {facilities.data && facilities.data.items.length === 0 && (
          <EmptyState message="No facilities registered." />
        )}
        {facilities.data && facilities.data.items.length > 0 && (
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
            {facilities.data.items.map((f) => (
              <FacilityCard
                key={f.id}
                code={f.code}
                name={f.name}
                serviceType={f.service_type}
                region={f.region}
                availability={f.availability_status}
                services={f.services}
              />
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="Active Referrals">
        {referrals.isPending && <LoadingState />}
        {referrals.isError && (
          <ErrorState message="Could not load referrals." />
        )}
        {referrals.data && referrals.data.items.length === 0 && (
          <EmptyState message="No referrals yet." />
        )}
        {referrals.data && referrals.data.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-xs uppercase text-slate-400">
                  <th className="py-2 px-3">Referral</th>
                  <th className="py-2 px-3">Type</th>
                  <th className="py-2 px-3">Status</th>
                  <th className="py-2 px-3">Facility</th>
                  <th className="py-2 px-3">Scheduled</th>
                  <th className="py-2 px-3">Feedback</th>
                </tr>
              </thead>
              <tbody>
                {referrals.data.items.map((r) => (
                  <ReferralRow
                    key={r.id}
                    referral={r}
                    onFeedback={(id, st) =>
                      feedback.mutate({ referralId: id, req: { receiving_status: st } })
                    }
                    pending={feedback.isPending}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>
    </div>
  )
}

export default FacilitiesPage
