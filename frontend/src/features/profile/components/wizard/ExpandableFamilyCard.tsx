import React, { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ExpandableFamilyCardProps {
  relative: string
  diseases: string[]
  onDiseasesChange: (diseases: string[]) => void
  ageAtDiagnosis: string
  onAgeAtDiagnosisChange: (value: string) => void
  currentStatus: string
  onCurrentStatusChange: (value: string) => void
  notes: string
  onNotesChange: (value: string) => void
}

const COMMON_DISEASES = [
  'Hypertension', 'Diabetes', 'Heart Disease', 'Cancer', 'Stroke',
  'Asthma', 'COPD', 'Kidney Disease', 'Thyroid Disease', 'Autoimmune Disease',
  'Alzheimer\'s', 'Parkinson\'s', 'Depression', 'Anxiety', 'Arthritis',
]

export function ExpandableFamilyCard({
  relative,
  diseases,
  onDiseasesChange,
  ageAtDiagnosis,
  onAgeAtDiagnosisChange,
  currentStatus,
  onCurrentStatusChange,
  notes,
  onNotesChange,
}: ExpandableFamilyCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [search, setSearch] = useState('')

  const toggleDisease = (disease: string) => {
    if (diseases.includes(disease)) {
      onDiseasesChange(diseases.filter((d) => d !== disease))
    } else {
      onDiseasesChange([...diseases, disease])
    }
  }

  const filtered = COMMON_DISEASES.filter((d) =>
    d.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden dark:border-slate-700 dark:bg-slate-800">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <div className="flex items-center gap-3">
          {expanded ? (
            <ChevronDown className="h-4 w-4 text-slate-400" />
          ) : (
            <ChevronRight className="h-4 w-4 text-slate-400" />
          )}
          <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">{relative}</span>
          {diseases.length > 0 ? (
            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[11px] font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
              {diseases.length}
            </span>
          ) : null}
        </div>
      </button>
      {expanded ? (
        <div className="border-t border-slate-100 px-4 py-3 space-y-3 dark:border-slate-700">
          <div>
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1.5">Diseases</label>
            <input
              type="text"
              placeholder="Search diseases..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
            />
            <div className="mt-2 flex flex-wrap gap-1.5">
              {filtered.map((disease) => {
                const active = diseases.includes(disease)
                return (
                  <button
                    key={disease}
                    type="button"
                    onClick={() => toggleDisease(disease)}
                    aria-pressed={active}
                    className={cn(
                      'rounded-full border px-2 py-0.5 text-[11px] font-medium transition-colors',
                      active
                        ? 'border-blue-500 bg-blue-500 text-white dark:bg-blue-600'
                        : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-300',
                    )}
                  >
                    {disease}
                  </button>
                )
              })}
            </div>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Age at Diagnosis</label>
              <input
                type="text"
                value={ageAtDiagnosis}
                onChange={(e) => onAgeAtDiagnosisChange(e.target.value)}
                placeholder="e.g. 2020"
                className="w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Current Status</label>
              <select
                value={currentStatus}
                onChange={(e) => onCurrentStatusChange(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
              >
                <option value="">Select...</option>
                <option value="alive">Alive</option>
                <option value="deceased">Deceased</option>
                <option value="unknown">Unknown</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">Notes</label>
            <textarea
              value={notes}
              onChange={(e) => onNotesChange(e.target.value)}
              placeholder="Additional notes..."
              rows={2}
              className="w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
            />
          </div>
        </div>
      ) : null}
    </div>
  )
}