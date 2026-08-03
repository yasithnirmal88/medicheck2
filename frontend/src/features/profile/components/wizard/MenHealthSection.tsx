import React from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Mars, Shield, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Field } from './FieldControl'
import type { FieldSpec } from './FieldControl'
import type { WizardState } from '@/features/profile/types/wizard'

interface MenHealthSectionProps {
  data: WizardState['men_health']
  onChange: (data: WizardState['men_health']) => void
}

const fieldSpecs: FieldSpec[] = [
  { name: 'prostate_issues', label: 'Prostate Issues', kind: 'emoji', options: [{ value: 'no', label: '😊 No' }, { value: 'bph', label: '⚠️ BPH' }, { value: 'prostatitis', label: '🔬 Prostatitis' }, { value: 'cancer', label: '🚨 Cancer' }], cols: 4, optional: true },
  { name: 'testosterone_therapy', label: 'Testosterone Therapy', kind: 'card', options: [{ value: 'no', label: '😊 No' }, { value: 'current', label: '💉 Currently on therapy' }, { value: 'former', label: '📋 Former therapy' }], cols: 3, optional: true },
  { name: 'urinary_symptoms', label: 'Urinary Symptoms', kind: 'emoji', options: [{ value: 'none', label: '😊 None' }, { value: 'mild', label: '😐 Mild' }, { value: 'moderate', label: '😴 Moderate' }, { value: 'severe', label: '😱 Severe' }], cols: 4, optional: true },
]

export function MenHealthSection({ data, onChange }: MenHealthSectionProps) {
  const record = data as Record<string, unknown>

  const update = (name: string, value: unknown) => {
    onChange({ ...record, [name]: value } as WizardState['men_health'])
  }

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key="men-health"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.3 }}
        className="space-y-6"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
            <Mars className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100">Men's Health</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">Prostate and hormonal health details</p>
          </div>
        </div>

        {fieldSpecs.map((spec) => (
          <Field key={spec.name} spec={spec} bag={{
            register: (name: string) => ({
              name,
              onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => update(name, e.target.value),
              onBlur: () => {},
              ref: () => {},
            }),
            setValue: update,
            watch: (name: string) => record[name],
            error: undefined,
          }} />
        ))}
      </motion.div>
    </AnimatePresence>
  )
}