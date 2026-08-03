import React from 'react'

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'ghost' | 'danger'
}

const classes = {
  primary: 'px-4 py-2 rounded bg-indigo-600 text-white hover:bg-indigo-700',
  ghost: 'px-4 py-2 rounded bg-transparent text-indigo-600',
  danger: 'px-4 py-2 rounded bg-red-600 text-white hover:bg-red-700',
}

const Button: React.FC<ButtonProps> = ({ variant = 'primary', className = '', children, ...rest }) => {
  return (
    <button className={`${classes[variant]} ${className}`} {...rest}>
      {children}
    </button>
  )
}

export default React.memo(Button)
