import React from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Baby, Calendar, Venus, Pill, Heart } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Field } from './FieldControl'
import type { FieldSpec } from './FieldControl'
import type { WizardState } from '@/features/profile/types/wizard'

interface WomenHealthSectionProps {
  data: WizardState['women_health']
  onChange: (data: WizardState['women_health']) => void
}

const fieldSpecs: FieldSpec[] = [
  { name: 'pregnancy', label: 'Current Pregnancy', kind: 'emoji', options: [{ value: 'no', label: '😊 No' }, { value: 'planning', label: '🤔 Planning' }, { value: 'pregnant', label: '🤰 Pregnant' }, { value: 'postpartum', label: '🍼 Postpartum' }], cols: 4 },
  { name: 'menstrual_cycle', label: 'Menstrual Cycle Regularity', kind: 'card', options: [{ value: 'regular', label: 'Regular' }, { value: 'irregular', label: 'Irregular' }, { value: 'absent', label: 'Absent' }], cols: 3, optional: true },
  { name: 'pcos', label: 'PCOS', kind: 'emoji', options: [{ value: 'no', label: '😊 No' }, { value: 'diagnosed', label: '⚕️ Diagnosed' }, { value: 'suspected', label: '🔍 Suspected' }], cols: 3, optional: true },
  { name: 'menopause', label: 'Menopause', kind: 'emoji', options: [{ value: 'no', label: '😊 No' }, { value: 'perimenopause', label: '🔄 Perimenopause' }, { value: 'postmenopause', label: '🧓 Postmenopause' }], cols: 3, optional: true },
  { name: 'contraception', label: 'Contraception', kind: 'card', options: [{ value: 'none', label: 'None' }, { value: 'pill', label: '💊 Pill' }, { value: 'iud', label: '🩺 IUD' }, { value: 'implant', label: '💉 Implant' }, { value: 'injection', label: '💉 Injection' }, { value: 'other', label: 'Other' }], cols: 3, optional: true },
  { name: 'pregnancy_history', label: 'Pregnancy History', kind: 'textarea', placeholder: 'Gravida/Para details, complications', cols: 2, optional: true, rows: 3 },
]

export function WomenHealthSection({ data, onChange }: WomenHealthSectionProps) {
  const record = data as unknown as Record<string, unknown>

  const update = (name: string, value: unknown) => {
    onChange({ ...record, [name]: value } as unknown as WizardState['women_health'])
  }

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key="women-health"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.3 }}
        className="space-y-6"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-pink-100 text-pink-600 dark:bg-pink-900/30 dark:text-pink-400">
            <Venus className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100">Women&apos;s Health</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">Reproductive and hormonal health details</p>
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
