import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { PatientLayout } from '../PatientLayout'
import { DoctorLayout } from '../DoctorLayout'

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
