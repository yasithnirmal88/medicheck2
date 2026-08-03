import React, { useMemo } from 'react'
import { cn } from '@/lib/utils'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  as?: 'div' | 'section' | 'article'
  padded?: boolean
  interactive?: boolean
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ as: Component = 'div', padded = true, interactive = false, className, children, ...rest }, ref) => {
    const Tag = Component as 'div'
    const classes = useMemo(
      () =>
        cn(
          'rounded-2xl border border-slate-200/80 bg-white shadow-sm',
          'dark:border-slate-700/60 dark:bg-slate-800/70',
          'transition-colors duration-200',
          padded && 'p-5',
          interactive && 'hover:shadow-md hover:border-slate-300 dark:hover:border-slate-600',
          className,
        ),
      [padded, interactive, className],
    )
    return (
      <Tag ref={ref} className={classes} {...rest}>
        {children}
      </Tag>
    )
  },
)

Card.displayName = 'Card'

export default React.memo(Card)