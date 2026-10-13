import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Providers from './providers/Providers'
import Router from './router'
import ErrorBoundary from './shared/ui/ErrorBoundary'
import './index.css'

// Retry only genuinely transient failures (network errors, 429, 5xx). Auth
// errors (401/403) and client errors (404/422) are not retried by TanStack so
// they fail fast instead of holding isLoading true for an extra attempt. The
// axios 401-refresh interceptor already handles token-expiry retry once.
function shouldRetryQuery(failureCount: number, error: unknown): boolean {
  if (failureCount >= 1) return false
  const status =
    (error as { response?: { status?: number } })?.response?.status ??
    (error as { status?: number })?.status
  if (status === undefined) return true // network error / timeout -> transient
  if (status === 429 || status >= 500) return true // rate-limited / server fault
  return false // 4xx (incl. 401/403/404) -> do not retry
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      gcTime: 10 * 60 * 1000,
      refetchOnWindowFocus: false,
      retry: shouldRetryQuery,
    }
  }
})

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Providers>
            <Router />
          </Providers>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>
)
