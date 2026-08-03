import React, { useState } from 'react'
import { Plus, X, CheckCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { AnimatePresence, motion } from 'framer-motion'

interface Vaccination {
  id: string
  vaccine: string
  dose: string
  date: string
  provider: string
}

const PREDEFINED_VACCINES = [
  { id: 'covid', label: 'COVID-19', icon: '🦠' },
  { id: 'influenza', label: 'Influenza', icon: '🩸' },
  { id: 'hepatitis', label: 'Hepatitis', icon: '🫁' },
  { id: 'hpv', label: 'HPV', icon: '🛡️' },
  { id: 'mmr', label: 'MMR', icon: '💉' },
  { id: 'tetanus', label: 'Tetanus', icon: '🔬' },
  { id: 'pneumococcal', label: 'Pneumococcal', icon: '🫁' },
]

interface VaccinationSectionProps {
  items: Vaccination[]
  onChange: (items: Vaccination[]) => void
}

export function VaccinationSection({ items, onChange }: VaccinationSectionProps) {
  const [customVaccine, setCustomVaccine] = useState('')

  const togglePredefined = (vaccineId: string) => {
    const existing = items.find((v) => v.vaccine === vaccineId)
    if (existing) {
      onChange(items.filter((v) => v.vaccine !== vaccineId))
    } else {
      const vaccine = PREDEFINED_VACCINES.find((v) => v.id === vaccineId)
      onChange([
        ...items,
        {
          id: crypto.randomUUID(),
          vaccine: vaccine?.label ?? vaccineId,
          dose: '',
          date: '',
          provider: '',
        },
      ])
    }
  }

  const addCustom = () => {
    if (!customVaccine.trim()) return
    onChange([
      ...items,
      {
        id: crypto.randomUUID(),
        vaccine: customVaccine.trim(),
        dose: '',
        date: '',
        provider: '',
      },
    ])
    setCustomVaccine('')
  }

  const updateItem = (id: string, field: string, value: string) => {
    onChange(
      items.map((item) =>
        item.id === id ? { ...item, [field]: value } : item
      )
    )
  }

  const removeItem = (id: string) => {
    onChange(items.filter((item) => item.id !== id))
  }

  const isPredefined = (vaccineName: string) =>
    PREDEFINED_VACCINES.some((v) => v.label === vaccineName)

  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">Standard Vaccines</h4>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {PREDEFINED_VACCINES.map((v) => {
            const active = items.some((item) => item.vaccine === v.label)
            return (
              <button
                key={v.id}
                type="button"
                onClick={() => togglePredefined(v.id)}
                aria-pressed={active}
                className={cn(
                  'rounded-xl border p-3 text-left transition-all duration-200',
                  active
                    ? 'border-blue-500 bg-blue-50 shadow-sm dark:border-blue-400 dark:bg-blue-500/15'
                    : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800',
                )}
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">{v.icon}</span>
                  <span className={cn('text-sm font-medium', active ? 'text-blue-700 dark:text-blue-300' : 'text-slate-700 dark:text-slate-200')}>
                    {v.label}
                  </span>
                </div>
                {active ? (
                  <CheckCircle className="mt-1 h-3.5 w-3.5 text-blue-500" />
                ) : null}
              </button>
            )
          })}
        </div>
      </div>

      <div>
        <label className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-2">Custom Vaccine</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={customVaccine}
            onChange={(e) => setCustomVaccine(e.target.value)}
            placeholder="e.g. Shingles, Malaria"
            className="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                addCustom()
              }
            }}
          />
          <button
            type="button"
            onClick={addCustom}
            className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
      </div>

      <AnimatePresence>
        {items.map((item) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="relative rounded-xl border border-slate-200 bg-white p-4 space-y-3 dark:border-slate-700 dark:bg-slate-800"
          >
            <button
              type="button"
              onClick={() => removeItem(item.id)}
              className="absolute top-3 right-3 rounded-full p-1 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              aria-label="Remove vaccination"
            >
              <X className="h-4 w-4" />
            </button>

            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                {isPredefined(item.vaccine) ? '🛡️' : '💉'} {item.vaccine}
              </span>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">Dose</label>
                <input
                  value={item.dose}
                  onChange={(e) => updateItem(item.id, 'dose', e.target.value)}
                  placeholder="e.g. 1st dose"
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
                />
              </div>
              <div>
                <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">Date</label>
                <input
                  type="date"
                  value={item.date}
                  onChange={(e) => updateItem(item.id, 'date', e.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1">Provider</label>
                <input
                  value={item.provider}
                  onChange={(e) => updateItem(item.id, 'provider', e.target.value)}
                  placeholder="e.g. City Health Clinic"
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:focus:border-blue-400"
                />
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}