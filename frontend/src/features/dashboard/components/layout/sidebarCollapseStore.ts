/**
 * Sidebar collapse state — shared, persisted, role-aware.
 *
 * Why: the single RootLayout hosts both patient and doctor chrome. Each
 * role's sidebar collapse preference is kept in its own tiny external
 * store (module state + localStorage) so the preference survives page
 * transitions AND survives the (rare) role switch, without conflating
 * the two roles' preferences. Consumers subscribe via
 * useSyncExternalStore, so every mounted chrome re-renders on toggle.
 *
 * Desktop only. The mobile drawer is independently open/closed per
 * navigation and intentionally NOT persisted.
 */

const PATIENT_STORAGE_KEY = 'medicheck_sidebar_collapsed'
const DOCTOR_STORAGE_KEY = 'medicheck_doctor_sidebar_collapsed'

function readInitial(key: string): boolean {
  try {
    return localStorage.getItem(key) === '1'
  } catch {
    return false
  }
}

interface CollapseStore {
  get(): boolean
  subscribe(listener: () => void): () => void
  set(next: boolean): void
  toggle(): void
}

function createCollapseStore(key: string): CollapseStore {
  let collapsed = readInitial(key)
  const listeners = new Set<() => void>()

  function emit() {
    listeners.forEach((l) => l())
  }

  function persist(next: boolean) {
    collapsed = next
    try {
      localStorage.setItem(key, next ? '1' : '0')
    } catch {
      // ignore storage errors (private mode, quota)
    }
    emit()
  }

  return {
    get: () => collapsed,
    subscribe(listener: () => void) {
      listeners.add(listener)
      return () => {
        listeners.delete(listener)
      }
    },
    set(next: boolean) {
      if (next === collapsed) return
      persist(next)
    },
    toggle() {
      persist(!collapsed)
    },
  }
}

const patientStore = createCollapseStore(PATIENT_STORAGE_KEY)
const doctorStore = createCollapseStore(DOCTOR_STORAGE_KEY)

// --- Patient sidebar (existing public API preserved) ---

export function setSidebarCollapsed(next: boolean) {
  patientStore.set(next)
}

export function toggleSidebarCollapsed() {
  patientStore.toggle()
}

export function getSidebarCollapsed(): boolean {
  return patientStore.get()
}

export function subscribeSidebarCollapsed(listener: () => void): () => void {
  return patientStore.subscribe(listener)
}

// --- Doctor/CMS sidebar ---

export function setDoctorSidebarCollapsed(next: boolean) {
  doctorStore.set(next)
}

export function toggleDoctorSidebarCollapsed() {
  doctorStore.toggle()
}

export function getDoctorSidebarCollapsed(): boolean {
  return doctorStore.get()
}

export function subscribeDoctorSidebarCollapsed(listener: () => void): () => void {
  return doctorStore.subscribe(listener)
}
