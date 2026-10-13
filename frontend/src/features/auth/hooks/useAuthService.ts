/**
 * Auth API - migrated onto the generated, schema-derived client.
 *
 * Second worked example of the migration pattern (see
 * `features/profile/api/profileService.ts` for the first).
 *
 * The payoff here is the role enum. The backend `UserResponse.roles` is typed
 * `string[]` because the RBAC layer returns whatever role codes are assigned,
 * and this project's Role enum is broader than the old four-value literal the
 * frontend used to assume. Consuming the generated `UserResponse` means the
 * frontend can no longer silently narrow roles it does not know about, which is
 * what previously made the CMS appear empty for a `medical_director`.
 */

import {
  getCurrentUserProfileApiV1UsersMeGet,
  type UserResponse,
} from '@/api'

/**
 * `GET /users/me` (and, equivalently, `/auth/me`).
 *
 * Returns the generated `UserResponse`, so `roles` is `string[]` - the shape the
 * backend actually sends. Role-to-permission mapping still lives in
 * `@/types/role`; this only guarantees the wire shape matches.
 */
export const fetchProfile = async (): Promise<UserResponse> =>
  getCurrentUserProfileApiV1UsersMeGet()