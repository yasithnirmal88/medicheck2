import { describe, it, expect } from 'vitest'
import {
  ROLE_DISPLAY_NAMES,
  ROLE_HIERARCHY,
  ROLE_CATEGORIES,
  isCHWRole,
  hasPermission,
} from '../role'

describe('UserRole type — Community Health Worker (Phase 8)', () => {
  it('includes the community_health_worker role', () => {
    expect(ROLE_DISPLAY_NAMES.community_health_worker).toBeTruthy()
  })

  it('categorizes the CHW role as "chw"', () => {
    expect(ROLE_CATEGORIES.community_health_worker).toBe('chw')
    expect(isCHWRole('community_health_worker')).toBe(true)
    expect(isCHWRole('patient')).toBe(false)
    expect(isCHWRole('medical_director')).toBe(false)
  })

  it('assigns CHW a priority below CMS roles', () => {
    // CHW is level 3; the CMS-gate role (read_only_reviewer) is higher.
    expect(ROLE_HIERARCHY.community_health_worker).toBeLessThan(
      ROLE_HIERARCHY.read_only_reviewer
    )
  })

  it('grants CHW assessment + profile permissions but not CMS', () => {
    expect(hasPermission('community_health_worker', 'assessment:write')).toBe(true)
    expect(hasPermission('community_health_worker', 'profile:read')).toBe(true)
    expect(hasPermission('community_health_worker', 'cms:read')).toBe(false)
  })
})
