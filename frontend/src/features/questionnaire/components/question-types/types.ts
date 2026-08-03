import type { FC } from 'react'
import type { Question } from '../../types'

/**
 * Shared props for every reusable question input component.
 *
 * Each component maps its strongly-typed `value` to a concrete type via the
 * generic param (e.g. `QuestionInputProps<string>` for single-select,
 * `QuestionInputProps<string[]>` for multi-select, `QuestionInputProps<number>`
 * for numeric/slider). The default of `unknown` keeps the QuestionRenderer
 * interop simple while still giving component authors type flexibility.
 */
export interface QuestionInputProps<T = unknown> {
  question: Question
  value: T | null
  onChange: (value: T) => void
  error?: string
  disabled?: boolean
  onSearch?: (query: string) => Promise<{ id: string; text: string; value: string }[]>
}

/** A question input component bound to the shared props shape. */
export type QuestionInputComponent<T = unknown> = FC<QuestionInputProps<T>>
