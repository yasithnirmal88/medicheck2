import React from 'react'
import { Activity, Brain, ClipboardList, HeartPulse, Network, ShieldCheck } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import ThemeToggle from '@/shared/ui/ThemeToggle'
import Logo from './Logo'

type Feature = {
  icon: LucideIcon
  title: string
  desc: string
}

const features: Feature[] = [
  { icon: ClipboardList, title: 'Adaptive Medical Questionnaire', desc: 'Dynamic, branching clinical intake tailored to each patient.' },
  { icon: Network, title: 'Clinical Knowledge Graph', desc: 'Structured links between symptoms, conditions, and evidence.' },
  { icon: Brain, title: 'Explainable AI Reports', desc: 'Transparent risk insights you can trace and trust.' },
  { icon: Activity, title: 'Health Timeline', desc: 'Follow your clinical history across multiple assessments.' },
  { icon: HeartPulse, title: 'Personalized Recommendations', desc: 'Guidance computed from your unique health profile.' },
  { icon: ShieldCheck, title: 'Secure Medical Data', desc: 'Protected, compliant, and encrypted at every layer.' },
]

type AuthLayoutProps = {
  children: React.ReactNode
}

const BrandPanel: React.FC = () => {
  return (
    <div className="flex min-h-full flex-col justify-between gap-8 p-8 sm:p-12 lg:p-16">
      <div className="animate-fade-in-up">
        <Logo variant="light" className="h-9" />
      </div>

      <div className="space-y-7">
        <div className="animate-fade-in-up">
          <p className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.2em] text-teal-300/90">
            <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-teal-300" aria-hidden="true" />
            AI-Powered Healthcare
          </p>
          <h1 className="mt-3 text-4xl font-bold leading-tight tracking-tight text-white sm:text-5xl">
            Predict. Prevent.
            <br />
            <span className="bg-gradient-to-r from-teal-300 to-blue-300 bg-clip-text text-transparent">
              Personalize.
            </span>
          </h1>
        </div>

        <p className="max-w-md text-base leading-relaxed text-blue-100/90 animate-fade-in-up">
          The Medicheck AI platform for early disease detection, adaptive medical questionnaires,
          clinical knowledge graphs, and explainable health insights.
        </p>

        <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 animate-fade-in-up">
          {features.map((feature) => (
            <li
              key={feature.title}
              className="group flex items-start gap-3 rounded-2xl border border-white/10 bg-white/5 p-3.5 backdrop-blur-sm transition-colors hover:bg-white/10"
            >
              <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/10 text-teal-300 transition-colors group-hover:bg-teal-400/20">
                <feature.icon className="h-4 w-4" aria-hidden="true" />
              </span>
              <span className="flex flex-col gap-0.5">
                <span className="text-sm font-semibold text-white">{feature.title}</span>
                <span className="text-xs leading-snug text-blue-100/70">{feature.desc}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="text-sm font-medium text-blue-100/70 animate-fade-in-up">v1.0 Beta</div>
    </div>
  )
}

const AuthLayout: React.FC<AuthLayoutProps> = ({ children }) => {
  return (
    <div className="relative min-h-screen w-full bg-slate-50 dark:bg-slate-950">
      <div className="lg:grid lg:grid-cols-[1.15fr_1fr]">
        {/* Left brand panel */}
        <aside className="relative hidden overflow-hidden bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 lg:block">
          <div className="absolute inset-0" aria-hidden="true">
            <div className="absolute -left-24 -top-24 h-96 w-96 rounded-full bg-blue-500/20 blur-3xl" />
            <div className="absolute bottom-0 right-0 h-[28rem] w-[28rem] rounded-full bg-teal-400/10 blur-3xl" />
            <div className="absolute left-1/3 top-1/2 h-72 w-72 rounded-full bg-indigo-500/10 blur-3xl" />
            <svg className="absolute inset-0 h-full w-full opacity-[0.04]" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <pattern id="medigrid" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M40 0H0v40" fill="none" stroke="white" strokeWidth="0.5" />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#medigrid)" />
            </svg>
          </div>
          <BrandPanel />
        </aside>

        {/* Right card panel */}
        <main className="relative flex min-h-screen items-center justify-center overflow-y-auto px-4 py-10 sm:px-8">
          <div className="absolute right-5 top-5 sm:top-6">
            <ThemeToggle />
          </div>

          <div className="w-full max-w-md animate-fade-in-up">
            {/* Mobile brand */}
            <div className="mb-8 flex justify-center lg:hidden">
              <Logo className="h-11" />
            </div>

            {children}
          </div>

          <p className="absolute bottom-4 left-0 right-0 text-center text-xs text-slate-400 dark:text-slate-500">
            &copy; 2026 Medicheck &middot;{' '}
            <a href="#" className="hover:text-slate-600 dark:hover:text-slate-300">Privacy Policy</a>
            &nbsp;&middot;&nbsp;
            <a href="#" className="hover:text-slate-600 dark:hover:text-slate-300">Terms</a>
          </p>
        </main>
      </div>
    </div>
  )
}

export default AuthLayout