import React, { useState } from 'react'
import { cn } from '@/lib/utils'

interface DiseaseCardGridProps {
  selected: string[]
  onChange: (diseases: string[]) => void
}

const DISEASES = [
  { id: 'hypertension', label: 'Hypertension', icon: '🫀', color: 'red' },
  { id: 'diabetes', label: 'Diabetes', icon: '🩸', color: 'amber' },
  { id: 'heart_disease', label: 'Heart Disease', icon: '❤️', color: 'red' },
  { id: 'kidney_disease', label: 'Kidney Disease', icon: '🫘', color: 'teal' },
  { id: 'cancer', label: 'Cancer', icon: '🔬', color: 'purple' },
  { id: 'asthma', label: 'Asthma', icon: '🫁', color: 'blue' },
  { id: 'copd', label: 'COPD', icon: '🫁', color: 'blue' },
  { id: 'stroke', label: 'Stroke', icon: '🧠', color: 'slate' },
  { id: 'liver_disease', label: 'Liver Disease', icon: '🫁', color: 'amber' },
  { id: 'thyroid_disease', label: 'Thyroid Disease', icon: '🔶', color: 'teal' },
  { id: 'autoimmune_disease', label: 'Autoimmune Disease', icon: '🛡️', color: 'purple' },
  { id: 'mental_illness', label: 'Mental Illness', icon: '🧠', color: 'blue' },
]

export function DiseaseCardGrid({ selected, onChange }: DiseaseCardGridProps) {
  const [search, setSearch] = useState('')

  const filtered = DISEASES.filter((d) =>
    d.label.toLowerCase().includes(search.toLowerCase())
  )

  const toggle = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter((d) => d !== id))
    } else {
      onChange([...selected, id])
    }
  }

  return (
    <div className="space-y-3">
      <input
        type="text"
        placeholder="Search diseases..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:focus:border-blue-400"
      />
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {filtered.map((disease) => {
          const active = selected.includes(disease.id)
          return (
            <button
              key={disease.id}
              type="button"
              onClick={() => toggle(disease.id)}
              aria-pressed={active}
              className={cn(
                'rounded-xl border p-3 text-left transition-all duration-200 hover:shadow-md',
                active
                  ? 'border-blue-500 bg-blue-50 shadow-sm dark:border-blue-400 dark:bg-blue-500/15'
                  : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800',
              )}
            >
              <div className="flex items-center gap-2">
                <span className="text-lg">{disease.icon}</span>
                <span className={cn('text-sm font-medium', active ? 'text-blue-700 dark:text-blue-300' : 'text-slate-700 dark:text-slate-200')}>
                  {disease.label}
                </span>
              </div>
              {active ? (
                <div className="mt-1 flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400">
                  <span>✓ Selected</span>
                </div>
              ) : null}
            </button>
          )
        })}
      </div>
      {filtered.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">No diseases match your search.</p>
      ) : null}
    </div>
  )
}