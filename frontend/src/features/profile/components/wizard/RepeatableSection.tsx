import React from 'react'
import { RepeatableList } from './RepeatableList'

interface RepeatableSectionProps<T> {
  title: string
  description?: string
  items: T[]
  onChange: (items: T[]) => void
  newItem: T
  renderItem: (item: T, index: number, onUpdate: (item: T) => void, onRemove: () => void) => React.ReactNode
  emptyLabel: string
  addLabel: string
}

export function RepeatableSection<T>({
  title,
  description,
  items,
  onChange,
  newItem,
  renderItem,
  emptyLabel,
  addLabel,
}: RepeatableSectionProps<T>) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100">{title}</h3>
        {description ? <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p> : null}
      </div>
      <RepeatableList
        items={items}
        onChange={onChange}
        renderItem={renderItem}
        emptyLabel={emptyLabel}
        addLabel={addLabel}
        newItem={newItem}
      />
    </div>
  )
}