import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { PatientLayout } from '../PatientLayout'
import { DoctorLayout } from '../DoctorLayout'
import { DashboardLayout } from '../DashboardLayout'

vi.mock('@/contexts/AuthContext', () => ({
  useAuthContext: () => ({
    user: { displayName: 'Jane Doe', email: 'jane@example.com' },
    role: 'patient',
    accountType: 'patient',
    loading: false,
    roleLoading: false,
    isAuthenticated: true,
    isPatient: true,
    canAccessCMS: false,
    setRole: vi.fn(),
    signOut: vi.fn(),
  }),
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
      } as unknown as MediaQueryList))
})

describe('PatientLayout renders nested route content', () => {
  it('shows the dashboard page via <Outlet/> when used as a layout element', () => {
    render(
      <MemoryRouter initialEntries={['/app']}>
        <Routes>
          <Route path="/app" element={<PatientLayout />}>
            <Route index element={<div>Patient Dashboard Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Patient Dashboard Content')).toBeInTheDocument()
  })
})

describe('DoctorLayout renders nested route content', () => {
  it('shows the CMS dashboard page via <Outlet/> when used as a layout element', () => {
    render(
      <MemoryRouter initialEntries={['/cms/dashboard']}>
        <Routes>
          <Route path="/cms" element={<DoctorLayout />}>
            <Route path="dashboard" element={<div>CMS Dashboard Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('CMS Dashboard Content')).toBeInTheDocument()
  })
})

describe('Sidebar collapse toggle', () => {
  it('PatientLayout renders a collapse button that shrinks the sidebar', () => {
    render(
      <MemoryRouter initialEntries={['/app']}>
        <Routes>
          <Route path="/app" element={<PatientLayout />}>
            <Route index element={<div>Patient Dashboard Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    const collapseBtn = screen.getByRole('button', { name: 'Collapse sidebar' })
    expect(collapseBtn).toBeInTheDocument()

    fireEvent.click(collapseBtn)
    expect(screen.getByRole('button', { name: 'Expand sidebar' })).toBeInTheDocument()
  })

  it('DoctorLayout renders a collapse button that shrinks the sidebar', () => {
    render(
      <MemoryRouter initialEntries={['/cms/dashboard']}>
        <Routes>
          <Route path="/cms" element={<DoctorLayout />}>
            <Route path="dashboard" element={<div>CMS Dashboard Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    const collapseBtn = screen.getByRole('button', { name: 'Collapse sidebar' })
    expect(collapseBtn).toBeInTheDocument()

    fireEvent.click(collapseBtn)
    expect(screen.getByRole('button', { name: 'Expand sidebar' })).toBeInTheDocument()
  })
})

describe('DashboardLayout single sidebar', () => {
  it('renders exactly one sidebar aside for patient content', () => {
    const { container } = render(
      <MemoryRouter>
        <DashboardLayout>
          <div>Patient Page Content</div>
        </DashboardLayout>
      </MemoryRouter>,
    )

    // The desktop sidebar is the only <aside> rendered (mobile drawer is portaled
    // and only renders when opened).
    expect(container.querySelectorAll('aside').length).toBe(1)
    expect(screen.getByText('Patient Page Content')).toBeInTheDocument()
  })
})
