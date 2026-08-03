import React, { useEffect } from 'react'
import Button from '@/shared/ui/Button'
import { cn } from '@/lib/utils'

interface NavigationButtonsProps {
  onNext: () => void
  onBack: () => void
  isFirst: boolean
  isLast: boolean
  isSubmitting: boolean
  canGoNext: boolean
}

const NavigationButtons: React.FC<NavigationButtonsProps> = ({
  onNext,
  onBack,
  isFirst,
  isLast,
  isSubmitting,
  canGoNext,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey && canGoNext && !isSubmitting) {
        e.preventDefault()
        onNext()
      }
      if ((e.key === 'Enter' && e.shiftKey) || e.key === 'ArrowLeft') {
        if (!isFirst) {
          e.preventDefault()
          onBack()
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onNext, onBack, isFirst, canGoNext, isSubmitting])

  return (
    <div className="flex items-center justify-between pt-6 border-t border-gray-200 dark:border-gray-700">
      <div>
        {!isFirst && (
          <Button
            type="button"
            variant="ghost"
            onClick={onBack}
            disabled={isSubmitting}
            className="min-h-[44px] min-w-[100px]"
            aria-label="Previous question"
          >
            <svg className="w-4 h-4 mr-2 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </Button>
        )}
      </div>
      <Button
        type="button"
        variant="primary"
        onClick={onNext}
        disabled={!canGoNext || isSubmitting}
        className={cn('min-h-[44px] min-w-[120px]', isLast && 'bg-green-600 hover:bg-green-700')}
        aria-label={isLast ? 'Submit questionnaire' : 'Next question'}
      >
        {isSubmitting ? (
          <span className="flex items-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Saving...
          </span>
        ) : isLast ? (
          <span className="flex items-center gap-2">
            Submit
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </span>
        ) : (
          <span className="flex items-center gap-2">
            Next
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </span>
        )}
      </Button>
    </div>
  )
}

export default React.memo(NavigationButtons)
