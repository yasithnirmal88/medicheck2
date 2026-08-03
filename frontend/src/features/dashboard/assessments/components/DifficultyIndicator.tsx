import { cn } from '@/lib/utils'
import type { Difficulty } from '../types'

const DIFFICULTY_CONFIG: Record<Difficulty, { label: string; bars: number; color: string }> = {
  Beginner: { label: 'Beginner', bars: 1, color: 'text-emerald-500' },
  Intermediate: { label: 'Intermediate', bars: 2, color: 'text-amber-500' },
  Advanced: { label: 'Advanced', bars: 3, color: 'text-rose-500' },
}

export const DifficultyIndicator = ({ difficulty }: { difficulty: Difficulty }) => {
  const cfg = DIFFICULTY_CONFIG[difficulty]
  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: cfg.bars }).map((_, i) => (
        <span key={i} className={cn('h-1.5 w-4 rounded-sm', cfg.color, 'bg-current')} />
      ))}
      {cfg.bars < 3 &&
        Array.from({ length: 3 - cfg.bars }).map((_, i) => (
          <span key={`empty-${i}`} className="h-1.5 w-4 rounded-sm bg-slate-200 dark:bg-slate-700" />
        ))}
      <span className="ml-1 text-[10px] font-medium text-gray-600 dark:text-gray-300">{cfg.label}</span>
    </div>
  )
}
