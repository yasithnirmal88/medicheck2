import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, renderHook, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { AuthProvider, useAuthContext, CURRENT_USER_QUERY_KEY } from '../AuthContext'

// vi.mock factories are hoisted above imports, so any values they reference
// must be created with vi.hoisted (also hoisted).
const {
  authStateListeners,
  meHandler,
  mockSignOut,
} = vi.hoisted(() => ({
  authStateListeners: [] as Array<(user: unknown | null) => void>,
  meHandler: vi.fn(async (_url?: string, _config?: unknown) => ({ data: { roles: ['patient'] } })),
  mockSignOut: vi.fn(async () => {
    // Emulate Firebase sign-out: notify listeners with null user.
    authStateListeners.forEach((cb) => cb(null))
  }),
}))

vi.mock('@/lib/firebase', () => ({
  getFirebaseAuth: () => ({ currentUser: null }),
  onAuthStateChanged: (_auth: unknown, cb: (u: unknown | null) => void) => {
    authStateListeners.push(cb)
    return () => {} // unsubscribe
  },
  signOut: mockSignOut,
}))

vi.mock('@/lib/api', () => ({
  default: {
    get: (url: string, config?: unknown) => meHandler(url, config),
  },
}))

function makeWrapper(client: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={client}>
        <AuthProvider>{children}</AuthProvider>
      </QueryClientProvider>
    )
  }
}

beforeEach(() => {
  authStateListeners.length = 0
  meHandler.mockClear()
  mockSignOut.mockClear()
})

describe('AuthContext /auth/me TanStack query (P2-3)', () => {
  it('fetches /auth/me once when a Firebase user becomes available', async () => {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false, gcTime: 0 } },
    })
    const { result } = renderHook(() => useAuthContext(), {
      wrapper: makeWrapper(client),
    })

    // No user yet -> no fetch.
    expect(meHandler).not.toHaveBeenCalled()

    // Simulate Firebase login.
    await act(async () => {
      authStateListeners.forEach((cb) => cb({ uid: 'u1' }))
    })

    // Wait for the query to resolve.
    await act(async () => {
      await vi.waitFor(() => expect(result.current.role).toBe('patient'))
    })

    expect(meHandler).toHaveBeenCalledTimes(1)
    expect(result.current.role).toBe('patient')
    expect(result.current.roleLoading).toBe(false)
  })

  it('does NOT refetch /auth/me on re-render (shared cache, staleTime)', async () => {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: 60000 } },
    })
    const { result, rerender } = renderHook(() => useAuthContext(), {
      wrapper: makeWrapper(client),
    })

    await act(async () => {
      authStateListeners.forEach((cb) => cb({ uid: 'u1' }))
    })
    await act(async () => {
      await vi.waitFor(() => expect(result.current.role).toBe('patient'))
    })
    expect(meHandler).toHaveBeenCalledTimes(1)

    // Re-render the consumer multiple times -> no additional /auth/me calls.
    rerender()
    rerender()
    rerender()
    expect(meHandler).toHaveBeenCalledTimes(1)

    // The query data is cached under the shared key.
    expect(client.getQueryData(CURRENT_USER_QUERY_KEY)).toEqual({ roles: ['patient'] })
  })

  it('refreshRole() triggers a single refetch', async () => {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: 60000 } },
    })
    const { result } = renderHook(() => useAuthContext(), {
      wrapper: makeWrapper(client),
    })

    await act(async () => {
      authStateListeners.forEach((cb) => cb({ uid: 'u1' }))
    })
    await act(async () => {
      await vi.waitFor(() => expect(result.current.role).toBe('patient'))
    })
    expect(meHandler).toHaveBeenCalledTimes(1)

    await act(async () => {
      await result.current.refreshRole()
    })
    expect(meHandler).toHaveBeenCalledTimes(2)
  })

  it('signOut removes the cached /auth/me and clears role', async () => {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: 60000 } },
    })
    const { result } = renderHook(() => useAuthContext(), {
      wrapper: makeWrapper(client),
    })

    await act(async () => {
      authStateListeners.forEach((cb) => cb({ uid: 'u1' }))
    })
    await act(async () => {
      await vi.waitFor(() => expect(result.current.role).toBe('patient'))
    })
    expect(client.getQueryData(CURRENT_USER_QUERY_KEY)).toBeTruthy()

    await act(async () => {
      await result.current.signOut()
    })

    // Cache dropped so a future login refetches fresh (no stale role leak).
    expect(client.getQueryData(CURRENT_USER_QUERY_KEY)).toBeUndefined()
    expect(result.current.role).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('renders children and provides auth state', () => {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false, gcTime: 0 } },
    })
    const Child = () => {
      const ctx = useAuthContext()
      return <div data-testid="state">{ctx.isAuthenticated ? 'yes' : 'no'}</div>
    }
    const { getByTestId } = render(
      <QueryClientProvider client={client}>
        <AuthProvider>
          <Child />
        </AuthProvider>
      </QueryClientProvider>
    )
    expect(getByTestId('state').textContent).toBe('no')
  })
})
