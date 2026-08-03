import React from 'react'
import { Check } from 'lucide-react'
import type { SectionKey } from '@/features/profile/types/wizard'

interface Step {
  key: SectionKey
  label: string
  icon: string
}

interface StepperProps {
  steps: Step[]
  currentStep: number
  onStepClick: (index: number) => void
}

export const Stepper: React.FC<StepperProps> = ({ steps, currentStep, onStepClick }) => {
  return (
    <nav aria-label="Wizard progress" className="mb-8">
      <ol className="flex items-center justify-between gap-2">
        {steps.map((step, index) => {
          const isActive = index === currentStep
          const isCompleted = index < currentStep
          const isClickable = index <= currentStep

          return (
            <li key={step.key} className="flex flex-1 items-center">
              <button
                type="button"
                onClick={() => isClickable ? onStepClick(index) : undefined}
                disabled={!isClickable}
                className={`flex w-full flex-col items-center gap-1.5 rounded-xl px-2 py-3 text-center transition-colors ${
                  isActive
                    ? 'bg-blue-50 dark:bg-blue-500/10'
                    : isCompleted
                      ? 'hover:bg-slate-50 dark:hover:bg-slate-800'
                      : 'opacity-40'
                } ${isClickable ? 'cursor-pointer' : 'cursor-default'}`}
                aria-current={isActive ? 'step' : undefined}
              >
                <span
                  className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold ${
                    isCompleted
                      ? 'bg-green-600 text-white'
                      : isActive
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-200 text-slate-500 dark:bg-slate-700 dark:text-slate-400'
                  }`}
                >
                  {isCompleted ? <Check className="h-4 w-4" /> : index + 1}
                </span>
                <span
                  className={`text-[11px] font-medium leading-tight ${
                    isActive
                      ? 'text-blue-600 dark:text-blue-400'
                      : isCompleted
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-slate-400 dark:text-slate-500'
                  }`}
                >
                  {step.label}
                </span>
              </button>
              {index < steps.length - 1 && (
                <div
                  className={`mx-1 mt-[-2rem] h-0.5 flex-1 ${
                    index < currentStep ? 'bg-green-500' : 'bg-slate-200 dark:bg-slate-700'
                  }`}
                />
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}