import React from 'react'
import { FieldError } from 'react-hook-form'
import { Check, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

export type FieldKind = 'text' | 'number' | 'select' | 'radio' | 'checkbox' | 'date' | 'textarea' | 'photo' | 'slider' | 'card' | 'chip' | 'emoji' | 'rating' | 'animated'

export interface OptionSpec {
  value: string
  label: string
}

export interface FieldSpec {
  name: string
  label: string
  kind: FieldKind
  options?: OptionSpec[]
  placeholder?: string
  suffix?: string
  help?: string
  warning?: string
  cols?: 1 | 2 | 3 | 4 | 5
  min?: number
  max?: number
  step?: number
  optional?: boolean
  asNumber?: boolean
  asDate?: boolean
  rows?: number
  type?: 'text' | 'email' | 'tel' | 'password'
}

export interface FieldRenderer {
  register: (name: string) => {
    name: string
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => void
    onBlur: () => void
    ref: React.Ref<HTMLInputElement>
  }
  setValue: (name: string, value: unknown) => void
  watch: (name: string) => unknown
}

type ElementProps<T extends HTMLElement> = {
  name: string
  onChange: React.ChangeEventHandler<T>
  onBlur: () => void
  ref: React.Ref<T>
}

function asElement<T extends HTMLElement>(field: ReturnType<FieldRenderer['register']>): ElementProps<T> {
  return field as unknown as ElementProps<T>
}

export interface FieldBag {
  register: FieldRenderer['register']
  setValue: FieldRenderer['setValue']
  watch: (name: string) => unknown
  error: FieldError | undefined
}

const inputBase = cn(
  'w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm transition',
  'placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20',
  'dark:border-slate-700 dark:bg-slate-800/70 dark:text-slate-200 dark:focus:border-blue-400',
  'disabled:cursor-not-allowed disabled:opacity-60',
)

export const Field: React.FC<{ spec: FieldSpec; bag: FieldBag; className?: string }> = ({ spec, bag, className }) => {
  const { register, setValue, error } = bag
  const hasError = Boolean(error)

  const common = cn(
    spec.kind === 'select' ? 'appearance-none' : '',
    hasError ? 'border-red-400 focus:border-red-400 focus:ring-red-500/20' : '',
  )

  const render = () => {
    switch (spec.kind) {
      case 'select':
        return (
          <div className="relative">
            <select
              {...asElement<HTMLSelectElement>(register(spec.name))}
              className={cn(inputBase, common, 'pr-8')}
              aria-invalid={hasError}
            >
              <option value="">{spec.optional ? 'Optional' : 'Select…'}</option>
              {spec.options?.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          </div>
        )
      case 'radio':
        return (
          <div className={cn('flex flex-wrap gap-2', spec.cols === 3 && 'grid grid-cols-2 sm:grid-cols-3')}>
            {spec.options?.map((opt) => {
              const active = bag.watch(spec.name) === opt.value
              return (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setValue(spec.name, opt.value)}
                  aria-pressed={active}
                  className={cn(
                    'rounded-xl border px-3 py-2 text-sm font-medium transition-colors',
                    active
                      ? 'border-blue-600 bg-blue-50 text-blue-700 dark:border-blue-400 dark:bg-blue-500/15 dark:text-blue-300'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300',
                  )}
                >
                  {opt.label}
                </button>
              )
            })}
          </div>
        )
      case 'slider':
        return (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <input
                type="range"
                min={spec.min ?? 0}
                max={spec.max ?? 100}
                step={spec.step ?? 1}
                value={(bag.watch(spec.name) as string) ?? spec.min ?? 0}
                onChange={(e) => setValue(spec.name, e.target.value)}
                className="flex-1 accent-blue-600 dark:accent-blue-400"
                aria-invalid={hasError}
              />
              <span className="ml-3 min-w-[3ch] text-right text-sm font-medium text-blue-600 dark:text-blue-400">
                {String(bag.watch(spec.name) ?? spec.min ?? 0)}{spec.suffix ?? ''}
              </span>
            </div>
            <div className="flex justify-between text-[11px] text-slate-400">
              <span>{spec.min ?? 0}{spec.suffix ?? ''}</span>
              <span>{spec.max ?? 100}{spec.suffix ?? ''}</span>
            </div>
          </div>
        )
      case 'card':
        return (
          <div className={cn('grid gap-3', spec.cols === 3 ? 'grid-cols-1 sm:grid-cols-3' : spec.cols === 2 ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1')}>
            {spec.options?.map((opt) => {
              const active = bag.watch(spec.name) === opt.value
              return (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setValue(spec.name, opt.value)}
                  aria-pressed={active}
                  className={cn(
                    'rounded-xl border px-4 py-3 text-left text-sm font-medium transition-colors',
                    active
                      ? 'border-blue-600 bg-blue-50 text-blue-700 dark:border-blue-400 dark:bg-blue-500/15 dark:text-blue-300'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700',
                  )}
                >
                  {opt.label}
                </button>
              )
            })}
          </div>
        )
      case 'chip':
        return (
          <div className="flex flex-wrap gap-2">
            {spec.options?.map((opt) => {
              const active = bag.watch(spec.name) === opt.value
              return (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setValue(spec.name, opt.value)}
                  aria-pressed={active}
                  className={cn(
                    'rounded-full border px-3 py-1.5 text-sm font-medium transition-colors',
                    active
                      ? 'border-blue-600 bg-blue-600 text-white dark:border-blue-400 dark:bg-blue-500'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300',
                  )}
                >
                  {opt.label}
                </button>
              )
            })}
          </div>
        )
      case 'emoji':
        return (
          <div className="flex flex-wrap gap-2">
            {spec.options?.map((opt) => {
              const active = bag.watch(spec.name) === opt.value
              return (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setValue(spec.name, opt.value)}
                  aria-pressed={active}
                  className={cn(
                    'rounded-xl border px-4 py-2 text-lg font-medium transition-all duration-200',
                    active
                      ? 'border-blue-500 bg-blue-50 scale-110 shadow-md dark:border-blue-400 dark:bg-blue-500/15'
                      : 'border-slate-200 bg-white hover:border-slate-300 hover:scale-105 dark:border-slate-700 dark:bg-slate-800',
                  )}
                >
                  {opt.label}
                </button>
              )
            })}
          </div>
        )
      case 'rating':
        return (
          <div className="flex gap-1">
            {Array.from({ length: spec.max ?? 5 }, (_, i) => {
              const val = i + 1
              const current = Number(bag.watch(spec.name)) || 0
              const filled = val <= current
              return (
                <button
                  key={val}
                  type="button"
                  onClick={() => setValue(spec.name, String(val))}
                  className={cn(
                    'text-2xl transition-colors duration-200',
                    filled ? 'text-amber-400' : 'text-slate-200 dark:text-slate-600',
                  )}
                  aria-label={`Rate ${val} of ${spec.max ?? 5}`}
                >
                  {filled ? '★' : '☆'}
                </button>
              )
            })}
            <span className="ml-2 self-center text-sm text-slate-500 dark:text-slate-400">
              {String(bag.watch(spec.name) ?? '—')}
            </span>
          </div>
        )
      case 'animated':
        return (
          <div className={cn('grid gap-3', spec.cols === 3 ? 'grid-cols-1 sm:grid-cols-3' : spec.cols === 2 ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1')}>
            {spec.options?.map((opt) => {
              const active = bag.watch(spec.name) === opt.value
              return (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setValue(spec.name, opt.value)}
                  aria-pressed={active}
                  className={cn(
                    'rounded-xl border p-4 text-left transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5',
                    active
                      ? 'border-blue-500 bg-blue-50 shadow-lg scale-[1.02] dark:border-blue-400 dark:bg-blue-500/15'
                      : 'border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800',
                  )}
                >
                  <div className="text-lg font-semibold text-slate-700 dark:text-slate-200">{opt.label}</div>
                </button>
              )
            })}
          </div>
        )
      case 'checkbox':
        return (
          <button
            type="button"
            onClick={() => setValue(spec.name, !bag.watch(spec.name))}
            aria-pressed={Boolean(bag.watch(spec.name))}
            className="inline-flex items-center gap-2 text-sm text-slate-700 dark:text-slate-200"
          >
            <span
              className={cn(
                'flex h-5 w-5 items-center justify-center rounded-md border transition-colors',
                bag.watch(spec.name)
                  ? 'border-blue-600 bg-blue-600 text-white'
                  : 'border-slate-300 bg-white dark:border-slate-600 dark:bg-slate-800',
              )}
            >
              {bag.watch(spec.name) ? <Check className="h-3.5 w-3.5" /> : null}
            </span>
            {spec.label}
          </button>
        )
      case 'textarea':
        return (
          <textarea
            {...asElement<HTMLTextAreaElement>(register(spec.name))}
            rows={spec.rows ?? 3}
            className={cn(inputBase, common)}
            placeholder={spec.placeholder}
            aria-invalid={hasError}
          />
        )
      default:
        return (
          <div className="relative">
            <input
              {...register(spec.name)}
              type={spec.type ?? (spec.kind === 'number' ? 'number' : spec.kind === 'date' ? 'date' : 'text')}
              inputMode={spec.kind === 'number' ? 'decimal' : undefined}
              step={spec.kind === 'number' ? spec.step : undefined}
              min={spec.kind === 'number' ? spec.min : undefined}
              max={spec.kind === 'number' ? spec.max : undefined}
              placeholder={spec.placeholder}
              className={cn(inputBase, common)}
              aria-invalid={hasError}
            />
            {spec.suffix ? (
              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400">
                {spec.suffix}
              </span>
            ) : null}
          </div>
        )
    }
  }

  return (
    <div className={cn('space-y-1.5', className)}>
      <label className="flex items-center justify-between gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
        <span>{spec.label}</span>
        {spec.optional ? <span className="text-[11px] font-normal text-slate-400">optional</span> : null}
      </label>
      {render()}
      {error ? <p className="text-xs text-red-600 dark:text-red-400">{error.message}</p> : null}
      {spec.help && !error ? (
        <p className="flex items-start gap-1.5 text-xs text-slate-500 dark:text-slate-400">
          <InfoIcon />
          {spec.help}
        </p>
      ) : null}
      {spec.warning && !error ? <p className="text-xs text-amber-600 dark:text-amber-400">{spec.warning}</p> : null}
    </div>
  )
}

function InfoIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="mt-0.5 h-3.5 w-3.5 shrink-0 text-teal-500">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 16v-4M12 8h.01" strokeLinecap="round" />
    </svg>
  )
}

export const Grid: React.FC<{ cols?: 1 | 2 | 3; children: React.ReactNode }> = ({ cols = 2, children }) => (
  <div className={cn('grid gap-4', cols === 1 ? 'grid-cols-1' : cols === 3 ? 'sm:grid-cols-3' : 'grid-cols-1 sm:grid-cols-2')}>
    {children}
  </div>
)