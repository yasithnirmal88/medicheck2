import React from 'react'
import { Plus, Trash2 } from 'lucide-react'

interface RepeatableListProps<T> {
  items: T[]
  onChange: (items: T[]) => void
  renderItem: (item: T, index: number, onUpdate: (item: T) => void, onRemove: () => void) => React.ReactNode
  emptyLabel: string
  addLabel: string
  newItem: T
}

export function RepeatableList<T>({ items, onChange, renderItem, emptyLabel, addLabel, newItem }: RepeatableListProps<T>) {
  const add = () => onChange([...items, newItem])
  const update = (index: number, item: T) => {
    const next = [...items]
    next[index] = item
    onChange(next)
  }
  const remove = (index: number) => onChange(items.filter((_, i) => i !== index))

  return (
    <div className="space-y-3">
      {items.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">{emptyLabel}</p>
      ) : null}
      {items.map((item, index) => (
        <div key={index} className="relative rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
          {renderItem(item, index, (updated) => update(index, updated), () => remove(index))}
          <button
            type="button"
            onClick={() => remove(index)}
            className="absolute top-3 right-3 rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-500/10 dark:hover:text-red-400"
            aria-label="Remove item"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ))}
      <button
            type="button"
            onClick={add}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-600 transition-colors hover:border-blue-500 hover:bg-blue-50/50 hover:text-blue-600 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:border-blue-500 dark:hover:bg-blue-500/10 dark:hover:text-blue-400"
          >
            <Plus className="h-4 w-4" />
            {addLabel}
          </button>
    </div>
  )
}