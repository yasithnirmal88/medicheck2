import React from 'react'
import { X, Pill } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MedicationCardProps {
  medication: string
  dosage: string
  frequency: string
  reason: string
  startDate: string
  prescribingDoctor: string
  currentStatus: string
  onUpdate: (field: string, value: string) => void
  onRemove: () => void
}

export function MedicationCard({
  medication,
  dosage,
  frequency,
  reason,
  startDate,
  prescribingDoctor,
  currentStatus,
  onUpdate,
  onRemove,
}: MedicationCardProps) {
  return (
    <div className="relative rounded-xl border border-slate-200 bg-white p-4 space-y-3 transition-shadow hover:shadow-md dark:border-slate-700 dark:bg-slate-800">
      <button
        type="button"
        onClick={onRemove}
        className="absolute top-3 right-3 rounded-full p-1 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
        aria-label="Remove medication"
      >
        <X className="h-4 w-4" />
      </button>

      <div className="flex items-center gap-2 mb-2">
        <Pill className="h-4 w-4 text-blue-500" />
        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200">Medication</h4>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">Medicine Name</label>
          <input
            value={medication}
            onChange={(e) => onUpdate('medication', e.target.value)}
            placeholder="e.g. Lisinopril"
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
          />
        </div>
        <div>
          <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">Dosage</label>
          <input
            value={dosage}
            onChange={(e) => onUpdate('dosage', e.target.value)}
            placeholder="e.g. 10mg"
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
          />
        </div>
        <div>
          <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">Frequency</label>
          <input
            value={frequency}
            onChange={(e) => onUpdate('frequency', e.target.value)}
            placeholder="e.g. Once daily"
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
          />
        </div>
        <div>
          <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">Reason</label>
          <input
            value={reason}
            onChange={(e) => onUpdate('reason', e.target.value)}
            placeholder="e.g. Blood pressure"
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
          />
        </div>
        <div>
          <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => onUpdate('start_date', e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
          />
        </div>
        <div>
          <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">Prescribing Doctor</label>
          <input
            value={prescribingDoctor}
            onChange={(e) => onUpdate('prescribing_doctor', e.target.value)}
            placeholder="e.g. Dr. Smith"
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
          />
        </div>
      </div>

      <div>
        <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">Current Status</label>
        <select
          value={currentStatus}
          onChange={(e) => onUpdate('current_status', e.target.value)}
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
        >
          <option value="">Select status...</option>
          <option value="active">Active</option>
          <option value="completed">Completed</option>
          <option value="discontinued">Discontinued</option>
          <option value="as_needed">As Needed</option>
        </select>
      </div>
    </div>
  )
}