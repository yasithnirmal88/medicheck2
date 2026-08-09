/**
 * Landing Page - Account Type Selection
 * 
 * Entry point for the application.
 * Users must select their account type (Patient or Doctor) before proceeding.
 */

import React from 'react'
import { useNavigate } from 'react-router-dom'
import { ShieldPlus, Stethoscope, ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import AuthLayout from '../components/AuthLayout'
import Button from '@/shared/ui/Button'

type AccountType = 'patient' | 'doctor'

const LandingPage: React.FC = () => {
  const navigate = useNavigate()

  const handleSelectAccountType = (type: AccountType) => {
    // Store selection in session storage for the registration flow
    sessionStorage.setItem('selected_account_type', type)
    
    // Navigate to appropriate login/register
    navigate(`/register?type=${type}`)
  }

  return (
    <AuthLayout>
      <div className="flex flex-col items-center justify-center min-h-[80vh] px-4">
        {/* Logo and Branding */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-teal-500 text-white shadow-lg">
              <ShieldPlus className="h-8 w-8" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
            Medicheck
          </h1>
          <p className="mt-2 text-slate-500 dark:text-slate-400">
            Healthcare Risk Assessment Platform
          </p>
        </div>

        {/* Account Type Selection */}
        <div className="w-full max-w-lg">
          <div className="text-center mb-8">
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
              Choose your account type
            </h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Select how you&rsquo;ll be using Medicheck
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {/* Patient Card */}
            <button
              onClick={() => handleSelectAccountType('patient')}
              className={cn(
                'group relative overflow-hidden rounded-2xl border-2 p-6 text-left transition-all duration-200',
                'hover:border-teal-500 hover:shadow-lg hover:-translate-y-1',
                'dark:border-slate-700 dark:hover:border-teal-400',
                'focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2'
              )}
            >
              {/* Background gradient */}
              <div className="absolute inset-0 bg-gradient-to-br from-teal-50 to-cyan-50 opacity-0 group-hover:opacity-100 transition-opacity dark:from-teal-900/20 dark:to-cyan-900/20" />
              
              <div className="relative">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-teal-100 text-teal-600 dark:bg-teal-900/50 dark:text-teal-300">
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                </div>
                
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                  Patient
                </h3>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                  Access health assessments, track your medical history, and receive personalized recommendations.
                </p>

                <div className="mt-4 flex items-center text-sm font-medium text-teal-600 dark:text-teal-400">
                  <span>Get Started</span>
                  <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                </div>
              </div>
            </button>

            {/* Doctor Card */}
            <button
              onClick={() => handleSelectAccountType('doctor')}
              className={cn(
                'group relative overflow-hidden rounded-2xl border-2 p-6 text-left transition-all duration-200',
                'hover:border-blue-500 hover:shadow-lg hover:-translate-y-1',
                'dark:border-slate-700 dark:hover:border-blue-400',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
              )}
            >
              {/* Background gradient */}
              <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-indigo-50 opacity-0 group-hover:opacity-100 transition-opacity dark:from-blue-900/20 dark:to-indigo-900/20" />
              
              <div className="relative">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 text-blue-600 dark:bg-blue-900/50 dark:text-blue-300">
                  <Stethoscope className="h-6 w-6" />
                </div>
                
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                  Healthcare Provider
                </h3>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                  Manage medical content, build assessment workflows, and review patient health data.
                </p>

                <div className="mt-4 flex items-center text-sm font-medium text-blue-600 dark:text-blue-400">
                  <span>Get Started</span>
                  <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                </div>
              </div>
            </button>
          </div>

          {/* Already have an account? */}
          <div className="mt-8 text-center">
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Already have an account?{' '}
              <button
                onClick={() => navigate('/login')}
                className="font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
              >
                Sign in
              </button>
            </p>
          </div>
        </div>

        {/* Features highlights */}
        <div className="mt-16 grid max-w-3xl grid-cols-1 gap-8 md:grid-cols-3">
          <div className="text-center">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-teal-100 text-teal-600 dark:bg-teal-900/50 dark:text-teal-300">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h4 className="font-medium text-slate-900 dark:text-white">Secure & Private</h4>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Your health data is encrypted and protected
            </p>
          </div>
          
          <div className="text-center">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-blue-600 dark:bg-blue-900/50 dark:text-blue-300">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h4 className="font-medium text-slate-900 dark:text-white">AI-Powered</h4>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Advanced risk assessment algorithms
            </p>
          </div>
          
          <div className="text-center">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-indigo-100 text-indigo-600 dark:bg-indigo-900/50 dark:text-indigo-300">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h4 className="font-medium text-slate-900 dark:text-white">Evidence-Based</h4>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Built on clinical guidelines
            </p>
          </div>
        </div>
      </div>
    </AuthLayout>
  )
}

export default LandingPage
