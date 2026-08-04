/**
 * Register Page - Role-Aware Registration
 * 
 * Handles user registration with account type selection.
 * Account type is determined from URL query param or session storage.
 */

import React, { useState, useEffect } from 'react'
import { useForm, SubmitHandler } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { KeyRound, LogIn, Mail, ShieldPlus, Stethoscope, User } from 'lucide-react'
import AuthLayout from '../components/AuthLayout'
import Input from '@/shared/ui/Input'
import PasswordInput from '@/shared/ui/PasswordInput'
import LoadingButton from '@/shared/ui/LoadingButton'
import Alert from '@/shared/ui/Alert'
import { registerSchema } from '../schemas/register'
import type { RegisterFormValues } from '../types/auth'
import { useRegister, useGoogleLogin, getAuthErrorMessage } from '../hooks/useLogin'
import { cn } from '@/lib/utils'

const RegisterPage: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [accountType, setAccountType] = useState<'patient' | 'doctor'>('patient')

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(registerSchema),
    mode: 'onBlur',
  })

  const registerMutation = useRegister()
  const googleLogin = useGoogleLogin()

  // Get account type from URL or session storage
  useEffect(() => {
    const typeParam = searchParams.get('type')
    if (typeParam === 'doctor' || typeParam === 'patient') {
      setAccountType(typeParam)
    } else {
      // Check session storage
      const storedType = sessionStorage.getItem('selected_account_type')
      if (storedType === 'doctor' || storedType === 'patient') {
        setAccountType(storedType)
      }
    }
  }, [searchParams])

  const onEmailSubmit: SubmitHandler<RegisterFormValues> = async (values) => {
    try {
      await registerMutation.mutateAsync({
        ...values,
        role: accountType,
      })
      
      // Navigate based on role
      const redirectPath = accountType === 'patient' ? '/app' : '/cms/dashboard'
      navigate(redirectPath)
    } catch {
      // Error handled by mutation state
    }
  }

  const onGoogleSubmit = async () => {
    try {
      await googleLogin.mutateAsync()
      
      // Navigate based on stored role (user will need to be assigned a role)
      // For now, default to patient portal
      const storedType = sessionStorage.getItem('selected_account_type') || 'patient'
      const redirectPath = storedType === 'patient' ? '/app' : '/cms/dashboard'
      navigate(redirectPath)
    } catch {
      // Error handled by mutation state
    }
  }

  const errorMessage = registerMutation.error
    ? getAuthErrorMessage(registerMutation.error)
    : googleLogin.error
      ? getAuthErrorMessage(googleLogin.error)
      : null

  const isLoading = registerMutation.isPending || googleLogin.isPending

  return (
    <AuthLayout>
      <div className="space-y-6">
        {/* Account Type Badge */}
        <div className={cn(
          'inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-medium',
          accountType === 'patient'
            ? 'bg-teal-100 text-teal-700 dark:bg-teal-900/50 dark:text-teal-300'
            : 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
        )}>
          {accountType === 'patient' ? (
            <>
              <ShieldPlus className="h-4 w-4" />
              <span>Patient Account</span>
            </>
          ) : (
            <>
              <Stethoscope className="h-4 w-4" />
              <span>Healthcare Provider Account</span>
            </>
          )}
        </div>

        <div className="space-y-1.5 text-center lg:text-left">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Create your account
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {accountType === 'patient'
              ? 'Start your health assessment journey with Medicheck.'
              : 'Join our clinical team and help improve patient outcomes.'}
          </p>
        </div>

        {errorMessage && (
          <Alert variant="error" live>
            {errorMessage}
          </Alert>
        )}

        <form
          onSubmit={handleSubmit(onEmailSubmit)}
          className="flex flex-col gap-4"
          noValidate
        >
          <Input
            id="displayName"
            label="Full Name"
            type="text"
            autoComplete="name"
            placeholder="John Smith"
            icon={<User className="h-4 w-4" aria-hidden="true" />}
            error={errors.displayName?.message}
            {...register('displayName')}
          />

          <Input
            id="email"
            label="Email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            icon={<Mail className="h-4 w-4" aria-hidden="true" />}
            error={errors.email?.message}
            {...register('email')}
          />

          <PasswordInput
            id="password"
            label="Password"
            autoComplete="new-password"
            placeholder="Create a strong password"
            icon={<KeyRound className="h-4 w-4" aria-hidden="true" />}
            error={errors.password?.message}
            {...register('password')}
          />

          <PasswordInput
            id="confirmPassword"
            label="Confirm Password"
            autoComplete="new-password"
            placeholder="Confirm your password"
            icon={<KeyRound className="h-4 w-4" aria-hidden="true" />}
            error={errors.confirmPassword?.message}
            {...register('confirmPassword')}
          />

          <LoadingButton
            type="submit"
            fullWidth
            loading={isLoading}
            loadingText="Creating account…"
            startIcon={<LogIn className="h-4 w-4" aria-hidden="true" />}
          >
            Create Account
          </LoadingButton>
        </form>

        <div className="relative flex items-center gap-3">
          <div className="h-px flex-1 bg-slate-200 dark:bg-slate-700" />
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400 dark:text-slate-500">
            or continue with
          </span>
          <div className="h-px flex-1 bg-slate-200 dark:bg-slate-700" />
        </div>

        <LoadingButton
          type="button"
          variant="google"
          fullWidth
          loading={isLoading}
          loadingText="Connecting…"
          onClick={onGoogleSubmit}
        >
          <GoogleIcon />
          Google
        </LoadingButton>

        <p className="text-center text-sm text-slate-500 dark:text-slate-400">
          Already have an account?{' '}
          <Link
            to="/login"
            className="font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
          >
            Sign in
          </Link>
        </p>

        {/* Account Type Switcher */}
        <div className="border-t border-slate-200 pt-4 dark:border-slate-700">
          <p className="text-center text-xs text-slate-500 dark:text-slate-400">
            Are you a {accountType === 'patient' ? 'healthcare provider' : 'patient'}?{' '}
            <button
              onClick={() => {
                const newType = accountType === 'patient' ? 'doctor' : 'patient'
                setAccountType(newType)
                sessionStorage.setItem('selected_account_type', newType)
                navigate(`/register?type=${newType}`, { replace: true })
              }}
              className="font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
            >
              Switch to {accountType === 'patient' ? 'Healthcare Provider' : 'Patient'} account
            </button>
          </p>
        </div>

        {/* Terms Notice */}
        <p className="text-center text-xs text-slate-400 dark:text-slate-500">
          By creating an account, you agree to our{' '}
          <a href="/terms" className="underline hover:text-slate-600">
            Terms of Service
          </a>{' '}
          and{' '}
          <a href="/privacy" className="underline hover:text-slate-600">
            Privacy Policy
          </a>
        </p>
      </div>
    </AuthLayout>
  )
}

const GoogleIcon: React.FC = () => (
  <svg className="h-4 w-4" viewBox="0 0 24 24" aria-hidden="true">
    <path
      fill="#4285F4"
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.27-4.74 3.27-8.1z"
    />
    <path
      fill="#34A853"
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23z"
    />
    <path
      fill="#FBBC05"
      d="M5.84 14.1a6.59 6.59 0 0 1 0-4.2V7.06H2.18a10.97 10.97 0 0 0 0 9.88l3.66-2.84z"
    />
    <path
      fill="#EA4335"
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15A10.97 10.97 0 0 0 12 2 11 11 0 0 0 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
    />
  </svg>
)

export default RegisterPage
