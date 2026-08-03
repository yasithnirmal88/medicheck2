import React from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link, useNavigate } from 'react-router-dom'
import { KeyRound, LogIn, Mail } from 'lucide-react'
import AuthLayout from '../components/AuthLayout'
import Input from '@/shared/ui/Input'
import PasswordInput from '@/shared/ui/PasswordInput'
import LoadingButton from '@/shared/ui/LoadingButton'
import Alert from '@/shared/ui/Alert'
import { loginSchema } from '../schemas/login'
import type { LoginFormValues } from '../types/auth'
import { useLogin, useGoogleLogin, getAuthErrorMessage } from '../hooks/useLogin'

const LoginPage: React.FC = () => {
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    mode: 'onBlur',
  })

  const login = useLogin()
  const googleLogin = useGoogleLogin()

  const onEmailSubmit = async (values: LoginFormValues) => {
    try {
      await login.mutateAsync(values)
      navigate('/app')
    } catch {
      // surface below via login.error
    }
  }

  const onGoogleSubmit = async () => {
    try {
      await googleLogin.mutateAsync()
      navigate('/app')
    } catch {
      // surface below
    }
  }

  const errorMessage = login.error
    ? getAuthErrorMessage(login.error)
    : googleLogin.error
      ? getAuthErrorMessage(googleLogin.error)
      : null

  return (
    <AuthLayout>
      <div className="space-y-6">
          <div className="space-y-1.5 text-center lg:text-left">
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Welcome back
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Sign in to continue to your health dashboard.
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
              id="email"
              label="Email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              icon={<Mail className="h-4 w-4" aria-hidden="true" />}
              error={errors.email?.message}
              {...register('email')}
            />

            <div className="flex flex-col gap-1.5">
              <PasswordInput
                id="password"
                label="Password"
                autoComplete="current-password"
                placeholder="Enter your password"
                icon={<KeyRound className="h-4 w-4" aria-hidden="true" />}
                error={errors.password?.message}
                {...register('password')}
              />
              <div className="-mt-1 flex items-center justify-end">
                <Link
                  to="/forgot-password"
                  className="text-sm font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  Forgot password?
                </Link>
              </div>
            </div>

            <LoadingButton
              type="submit"
              fullWidth
              loading={login.isPending}
              loadingText="Signing in…"
              startIcon={<LogIn className="h-4 w-4" aria-hidden="true" />}
            >
              Sign in
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
            loading={googleLogin.isPending}
            loadingText="Connecting…"
            onClick={onGoogleSubmit}
          >
            <GoogleIcon />
            Google
          </LoadingButton>

          <p className="text-center text-sm text-slate-500 dark:text-slate-400">
            Don&apos;t have an account?{' '}
            <Link
              to="/register"
              className="font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
            >
              Register
            </Link>
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

export default LoginPage