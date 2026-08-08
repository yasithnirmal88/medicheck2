/**
 * Sidebar collapse state — shared across DashboardLayout instances.
 *
 * Why: each patient route mounts a fresh DashboardLayout, so a local useState
 * for the collapse toggle resets on every navigation. Persisting the preference
 * in a tiny external store (plus localStorage) keeps the sidebar collapsed
 * across page transitions, which is the "make the sidebar shrinkable" UX fix.
 *
 * Desktop only. The mobile drawer is independently open/closed per navigation
 * and intentionally NOT persisted.
 */

const STORAGE_KEY = 'medicheck_sidebar_collapsed'

function readInitial(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === '1'
  } catch {
    return false
  }
}

let collapsed = readInitial()
const listeners = new Set<() => void>()

function emit() {
  listeners.forEach((l) => l())
}

function persist(next: boolean) {
  collapsed = next
  try {
    localStorage.setItem(STORAGE_KEY, next ? '1' : '0')
  } catch {
    // ignore storage errors (private mode, quota)
  }
  emit()
}

export function setSidebarCollapsed(next: boolean) {
  if (next === collapsed) return
  persist(next)
}

export function toggleSidebarCollapsed() {
  persist(!collapsed)
}

export function getSidebarCollapsed(): boolean {
  return collapsed
}

export function subscribeSidebarCollapsed(listener: () => void): () => void {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}
