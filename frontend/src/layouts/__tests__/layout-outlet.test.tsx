import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { DoctorLayout } from '../DoctorLayout'
import { DashboardLayout } from '../DashboardLayout'
import AppLayout from '../AppLayout'

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

describe('DashboardLayout collapse persistence (P3-6)', () => {
  it('keeps the sidebar collapsed across remounts (navigation)', () => {
    // First mount: collapse the sidebar.
    const { unmount } = render(
      <MemoryRouter>
        <DashboardLayout>
          <div>Page A</div>
        </DashboardLayout>
      </MemoryRouter>,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Collapse sidebar' }))
    expect(screen.getByRole('button', { name: 'Expand sidebar' })).toBeInTheDocument()
    unmount()

    // Second mount (simulates navigating to another patient page which
    // remounts DashboardLayout): the sidebar must stay collapsed.
    render(
      <MemoryRouter>
        <DashboardLayout>
          <div>Page B</div>
        </DashboardLayout>
      </MemoryRouter>,
    )
    expect(screen.getByRole('button', { name: 'Expand sidebar' })).toBeInTheDocument()

    // Clean up the shared store so other tests start expanded.
    fireEvent.click(screen.getByRole('button', { name: 'Expand sidebar' }))
  })
})

describe('AppLayout passthrough (P3-6 — no double layout)', () => {
  it('renders only its children (no extra TopNav/footer) so DashboardLayout is the sole chrome', () => {
    const { container } = render(
      <MemoryRouter>
        <AppLayout>
          <div data-testid="child">Inner Content</div>
        </AppLayout>
      </MemoryRouter>,
    )

    // No nav bar / footer from AppLayout — just the child.
    expect(container.querySelector('header')).toBeNull()
    expect(container.querySelector('footer')).toBeNull()
    expect(screen.getByTestId('child')).toBeInTheDocument()
  })
})
