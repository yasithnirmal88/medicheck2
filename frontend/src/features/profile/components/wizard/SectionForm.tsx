import React from 'react'
import { Field } from './FieldControl'
import type { FieldSpec } from './FieldControl'
import type { SectionKey } from '@/features/profile/types/wizard'
import { fieldSpecs } from '@/features/profile/wizard/fieldSpecs'

interface SectionFormProps<T = unknown> {
  sectionKey: SectionKey
  data: T
  onChange: (data: T) => void
}

export function SectionForm<T = unknown>({ sectionKey, data, onChange }: SectionFormProps<T>) {
  const specs = fieldSpecs[sectionKey]
  const record = data as Record<string, unknown>

  const update = (name: string, value: unknown) => {
    onChange({ ...record, [name]: value } as T)
  }

  if (specs.length === 0) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">No fields defined for this section.</p>
  }

  const groupedByCols = new Map<1 | 2 | 3 | 4 | 5, FieldSpec[]>()
  for (const spec of specs) {
    const cols = spec.cols ?? 1
    const group = groupedByCols.get(cols) ?? []
    group.push(spec)
    groupedByCols.set(cols, group)
  }

  return (
    <div className="space-y-6">
      {Array.from(groupedByCols.entries()).sort(([a], [b]) => a - b).map(([cols, groupSpecs]) => (
        <div key={cols} className={cols === 1 ? 'space-y-4' : 'grid grid-cols-1 gap-4 sm:grid-cols-2'}>
          {groupSpecs.map((spec) => (
            <Field
              key={spec.name}
              spec={spec}
              bag={{
                register: (name: string) => ({
                  name,
                  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
                    update(name, e.target.value)
                  },
                  onBlur: () => {},
                  ref: () => {},
                }),
                setValue: update,
                watch: (name: string) => record[name],
                error: undefined,
              }}
            />
          ))}
        </div>
      ))}
    </div>
  )
}