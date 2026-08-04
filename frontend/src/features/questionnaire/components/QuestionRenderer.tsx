import React from 'react'
import type { Question } from '../types'
import { cn } from '@/lib/utils'
import SingleChoice from './question-types/SingleChoice'
import MultipleChoice from './question-types/MultipleChoice'
import YesNo from './question-types/YesNo'
import NumericInput from './question-types/NumericInput'
import DecimalInput from './question-types/DecimalInput'
import SliderInput from './question-types/SliderInput'
import DateInput from './question-types/DateInput'
import TimeInput from './question-types/TimeInput'
import DropdownInput from './question-types/DropdownInput'
import MultiSelectInput from './question-types/MultiSelectInput'
import FreeTextInput from './question-types/FreeTextInput'
import SearchInput from './question-types/SearchInput'
import FileUploadInput from './question-types/FileUploadInput'

interface QuestionRendererProps {
  question: Question
  value: unknown
  onChange: (value: unknown) => void
  error?: string
  disabled?: boolean
  onSearch?: (query: string) => Promise<{ id: string; text: string; value: string }[]>
}

interface ComponentProps {
  value: unknown
  onChange: (value: unknown) => void
  error?: string
  disabled?: boolean
  onSearch?: (query: string) => Promise<{ id: string; text: string; value: string }[]>
}

const typeMap: Record<string, React.FC<ComponentProps>> = {
  single_choice: SingleChoice,
  multiple_choice: MultipleChoice,
  yes_no: YesNo,
  numeric: NumericInput,
  decimal: DecimalInput,
  slider: SliderInput,
  date: DateInput,
  time: TimeInput,
  dropdown: DropdownInput,
  multi_select: MultiSelectInput,
  free_text: FreeTextInput,
  search: SearchInput,
  file_upload: FileUploadInput,
}

const QuestionRenderer: React.FC<QuestionRendererProps> = ({ question, value, onChange, error, disabled, onSearch }) => {
  const Component = typeMap[question.question_type]

  if (!Component) {
    return (
      <div className="p-4 border border-yellow-300 bg-yellow-50 dark:bg-yellow-950 rounded-lg">
        <p className="text-sm text-yellow-700 dark:text-yellow-300">
          Unsupported question type: <strong>{question.question_type}</strong>
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {question.text}
          {question.is_required && <span className="text-red-500 ml-1">*</span>}
        </h3>
        {question.description && (
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{question.description}</p>
        )}
        {question.tooltip && (
          <div className="flex items-center gap-1 mt-1">
            <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-xs text-gray-400">{question.tooltip}</p>
          </div>
        )}
      </div>
      <div className={cn(error && 'p-3 border border-red-300 rounded-lg bg-red-50 dark:bg-red-950')}>
        <Component
          question={question}
          value={value}
          onChange={onChange}
          error={error}
          disabled={disabled}
          onSearch={onSearch}
        />
      </div>
    </div>
  )
}

export default QuestionRenderer
