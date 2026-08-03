import React from 'react'
import { X, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AllergyCardProps {
  type: string
  substance: string
  severity: string
  reaction: string
  emergencyMedication: string
  onUpdate: (field: string, value: string) => void
  onRemove: () => void
}

const SEVERITY_COLORS: Record<string, string> = {
  mild: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  moderate: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  severe: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  life_threatening: 'bg-red-200 text-red-900 dark:bg-red-900/40 dark:text-red-200',
}

export function AllergyCard({
  type,
  substance,
  severity,
  reaction,
  emergencyMedication,
  onUpdate,
  onRemove,
}: AllergyCardProps) {
  return (
    <div className="relative rounded-xl border border-slate-200 bg-white p-4 space-y-3 transition-shadow hover:shadow-md dark:border-slate-700 dark:bg-slate-800">
      <button
        type="button"
        onClick={onRemove}
        className="absolute top-3 right-3 rounded-full p-1 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
        aria-label="Remove allergy"
      >
        <X className="h-4 w-4" />
      </button>

      <div className="flex items-center gap-2 mb-2">
        <AlertTriangle className="h-4 w-4 text-amber-500" />
        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200">Allergy</h4>
        {severity ? (
          <span className={cn('rounded-full px-2 py-0.5 text-[10px] font-bold uppercase', SEVERITY_COLORS[severity] ?? 'bg-slate-100 text-slate-800')}>
            {severity}
          </span>
        ) : null}
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">Type</label>
          <select
            value={type}
            onChange={(e) => onUpdate('type', e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
          >
            <option value="">Select type...</option>
            <option value="food">Food</option>
            <option value="drug">Drug</option>
            <option value="environmental">Environmental</option>
            <option value="insect">Insect Sting</option>
            <option value="latex">Latex</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div>
          <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">Substance</label>
          <input
            value={substance}
            onChange={(e) => onUpdate('substance', e.target.value)}
            placeholder="e.g. Peanuts, Penicillin"
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
          />
        </div>
        <div>
          <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">Severity</label>
          <select
            value={severity}
            onChange={(e) => onUpdate('severity', e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
          >
            <option value="">Select severity...</option>
            <option value="mild">Mild</option>
            <option value="moderate">Moderate</option>
            <option value="severe">Severe</option>
            <option value="life_threatening">Life-Threatening</option>
          </select>
        </div>
        <div>
          <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">Reaction</label>
          <input
            value={reaction}
            onChange={(e) => onUpdate('reaction', e.target.value)}
            placeholder="e.g. Hives, Anaphylaxis"
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
          />
        </div>
      </div>

      <div>
        <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">Emergency Medication</label>
        <input
          value={emergencyMedication}
          onChange={(e) => onUpdate('emergency_medication', e.target.value)}
          placeholder="e.g. EpiPen"
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
        />
      </div>
    </div>
  )
}