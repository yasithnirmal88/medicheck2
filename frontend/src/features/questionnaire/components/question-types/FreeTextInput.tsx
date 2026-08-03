import React, { useRef, useEffect } from 'react'
import type { Question } from '../../types'
import { cn } from '@/lib/utils'

interface FreeTextInputProps {
  question: Question
  value: string | null
  onChange: (value: string) => void
  error?: string
  disabled?: boolean
}

const FreeTextInput: React.FC<FreeTextInputProps> = ({ question, value, onChange, error, disabled }) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const rules = question.validation_rules
  const charCount = value?.length ?? 0

  const autoResize = () => {
    const ta = textareaRef.current
    if (ta) {
      ta.style.height = 'auto'
      ta.style.height = ta.scrollHeight + 'px'
    }
  }

  useEffect(() => {
    autoResize()
  }, [value])

  return (
    <div>
      <textarea
        ref={textareaRef}
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        rows={4}
        maxLength={rules?.max_length ?? undefined}
        aria-label={question.text}
        placeholder="Type your answer here..."
        className={cn(
          'w-full px-4 py-3 border rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 resize-none overflow-hidden',
          error && 'border-red-500'
        )}
      />
      <div className="flex justify-between mt-1">
        {rules && (rules.min_length !== undefined || rules.max_length !== undefined) && (
          <p className="text-xs text-gray-500">
            {rules.min_length !== undefined && `Min ${rules.min_length} chars`}
            {rules.min_length !== undefined && rules.max_length !== undefined && ' | '}
            {rules.max_length !== undefined && `Max ${rules.max_length} chars`}
          </p>
        )}
        <p className={cn('text-xs ml-auto', charCount > (rules?.max_length ?? 999) ? 'text-red-500' : 'text-gray-400')}>
          {charCount}{rules?.max_length ? ` / ${rules.max_length}` : ''}
        </p>
      </div>
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  )
}

export default React.memo(FreeTextInput)
