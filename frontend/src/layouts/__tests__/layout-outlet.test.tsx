import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { RootLayout } from '../RootLayout'

// Mutable auth state so tests can switch roles (patient <-> doctor)
// and assert that RootLayout renders the role-appropriate chrome.
const authState = vi.hoisted(() => ({
  current: {
    user: { displayName: 'Jane Doe', email: 'jane@example.com' },
    role: 'patient',
    accountType: 'patient',
    loading: false,
    roleLoading: false,
    error: null,
    isAuthenticated: true,
    isPatient: true,
    isDoctor: false,
    isCHW: false,
    canAccessCMS: false,
    setRole: vi.fn(),
    refreshRole: vi.fn(),
    clearError: vi.fn(),
    signOut: vi.fn(),
  },
}))

vi.mock('@/contexts/AuthContext', () => ({
  useAuthContext: () => authState.current,
}))

vi.mock('react-dom', async () => {
  const actual = await vi.importActual<typeof import('react-dom')>('react-dom')
  return { ...actual, createPortal: (node: React.ReactNode) => node }
})

vi.mock('@/lib/firebase', () => ({
  getFirebaseAuth: () => ({}),
  signOut: vi.fn(),
}))

vi.mock('@/providers/AuthProvider', () => ({
  useAuth: () => ({ user: { displayName: 'Jane Doe', email: 'jane@example.com' } }),
}))

vi.mock('@/providers/ThemeProvider', () => ({
  useTheme: () => ({ theme: 'light', toggle: vi.fn() }),
}))

beforeEach(() => {
  window.matchMedia =
    window.matchMedia ||
    (() =>
      ({
        matches: false,
        addEventListener: () => {},
        removeEventListener: () => {},
      }) as unknown as MediaQueryList)

  // Reset to the patient role before each test.
  authState.current = {
    ...authState.current,
    role: 'patient',
    isPatient: true,
    canAccessCMS: false,
  }
  localStorage.clear()
})

describe('RootLayout renders nested route content', () => {
  it('renders page content via <Outlet/> for patient routes', () => {
    render(
      <MemoryRouter initialEntries={['/app']}>
        <Routes>
          <Route element={<RootLayout />}>
            <Route path="/app" element={<div>Patient Dashboard Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Patient Dashboard Content')).toBeInTheDocument()
  })

  it('renders page content via <Outlet/> for doctor/CMS routes', () => {
    authState.current = {
      ...authState.current,
      role: 'medical_director',
      isPatient: false,
      canAccessCMS: true,
    }
    render(
      <MemoryRouter initialEntries={['/cms/dashboard']}>
        <Routes>
          <Route element={<RootLayout />}>
            <Route path="/cms/dashboard" element={<div>CMS Dashboard Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('CMS Dashboard Content')).toBeInTheDocument()
  })
})

describe('RootLayout role-based chrome switching', () => {
  it('renders the patient sidebar nav for a patient role', () => {
    render(
      <MemoryRouter initialEntries={['/app']}>
        <Routes>
          <Route element={<RootLayout />}>
            <Route path="/app" element={<div>Patient Dashboard Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    // Patient nav items (from the dashboard navConfig). "Health
    // Profile" is unique to the sidebar; "Questionnaires" also
    // appears in the mobile bottom nav, so allow multiple.
    expect(screen.getByText('Health Profile')).toBeInTheDocument()
    expect(screen.getAllByText('Questionnaires').length).toBeGreaterThan(0)
    // Doctor-only nav must NOT render for patients.
    expect(screen.queryByText('Question Builder')).not.toBeInTheDocument()
    expect(screen.queryByText('Doctor CMS')).not.toBeInTheDocument()
  })

  it('renders the doctor/CMS sidebar nav for a clinical role', () => {
    authState.current = {
      ...authState.current,
      role: 'medical_director',
      isPatient: false,
      canAccessCMS: true,
    }
    render(
      <MemoryRouter initialEntries={['/cms/dashboard']}>
        <Routes>
          <Route element={<RootLayout />}>
            <Route path="/cms/dashboard" element={<div>CMS Dashboard Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    // Doctor/CMS nav items (from the CMS doctorNavConfig). "Doctor
    // CMS" appears in both the sidebar brand and the header.
    expect(screen.getAllByText('Doctor CMS').length).toBeGreaterThan(0)
    expect(screen.getByText('Question Builder')).toBeInTheDocument()
    // Patient-only nav must NOT render for doctors.
    expect(screen.queryByText('Health Profile')).not.toBeInTheDocument()
  })

  it('renders exactly one sidebar aside per role (no double chrome)', () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/app']}>
        <Routes>
          <Route element={<RootLayout />}>
            <Route path="/app" element={<div>Patient Dashboard Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    // The desktop sidebar is the only <aside> (the mobile drawer is
    // portaled and only renders when opened).
    expect(container.querySelectorAll('aside').length).toBe(1)
  })
})

describe('Patient sidebar collapse (RootLayout)', () => {
  it('toggles the patient sidebar and keeps it collapsed across remounts (navigation)', () => {
    // First mount: collapse the sidebar.
    const { unmount } = render(
      <MemoryRouter initialEntries={['/app']}>
        <Routes>
          <Route element={<RootLayout />}>
            <Route path="/app" element={<div>Page A</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Collapse sidebar' }))
    expect(screen.getByRole('button', { name: 'Expand sidebar' })).toBeInTheDocument()
    unmount()

    // Second mount (simulates navigating to another patient page): the
    // RootLayout never unmounts in the app, but the persisted store
    // must keep the preference even if it did.
    render(
      <MemoryRouter initialEntries={['/assessments']}>
        <Routes>
          <Route element={<RootLayout />}>
            <Route path="/assessments" element={<div>Page B</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )
    expect(screen.getByRole('button', { name: 'Expand sidebar' })).toBeInTheDocument()

    // Clean up the shared store so other tests start expanded.
    fireEvent.click(screen.getByRole('button', { name: 'Expand sidebar' }))
  })
})

describe('Doctor sidebar collapse (RootLayout)', () => {
  it('toggles the doctor sidebar and keeps it collapsed across remounts', () => {
    authState.current = {
      ...authState.current,
      role: 'medical_director',
      isPatient: false,
      canAccessCMS: true,
    }

    // First mount: collapse the sidebar.
    const { unmount } = render(
      <MemoryRouter initialEntries={['/cms/dashboard']}>
        <Routes>
          <Route element={<RootLayout />}>
            <Route path="/cms/dashboard" element={<div>CMS Page A</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Collapse sidebar' }))
    expect(screen.getByRole('button', { name: 'Expand sidebar' })).toBeInTheDocument()
    unmount()

    // Second mount: preference persisted (separate doctor store key).
    render(
      <MemoryRouter initialEntries={['/cms/questions']}>
        <Routes>
          <Route element={<RootLayout />}>
            <Route path="/cms/questions" element={<div>CMS Page B</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )
    expect(screen.getByRole('button', { name: 'Expand sidebar' })).toBeInTheDocument()

    // Clean up the shared doctor store so other tests start expanded.
    fireEvent.click(screen.getByRole('button', { name: 'Expand sidebar' }))
  })
})
