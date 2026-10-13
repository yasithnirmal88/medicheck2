/**
 * Profile API - now types its payloads from the generated, schema-derived
 * client (`src/api`) instead of a hand-maintained interface.
 *
 * This module is the reference example of the migration pattern: keep the
 * exported function names and runtime behaviour identical, but source the types
 * from the backend OpenAPI schema so drift becomes a compile error.
 *
 * The payoff is concrete. This module used to declare:
 *
 *     interface PersonalInfoPayload {
 *       emergency_contact?: string   // WRONG
 *     }
 *
 * The backend stores `emergency_contact` as a JSON object
 * (`PersonalInfoDTO.emergency_contact` is `{ [key: string]: unknown } | null`),
 * so that shape would have 422'd on submit. The generated type is correct, so
 * the mistake is now impossible to reintroduce here.
 *
 * Note: `fetchMyProfile` deliberately keeps its previous loose return type.
 * `HealthProfileDTO` from the schema exposes only `personal_info`, while some
 * existing callers read `profile.nutrition` and pass `personal_info` into a
 * lifestyle form. Those are separate frontend-schema issues (see
 * docs/api-types.md); narrowing the return type here would break working UI,
 * which is out of scope for setting up codegen.
 */

import api from '@/lib/api'
import type { PersonalInfoDTO } from '@/api'

/**
 * Body for `POST /profiles/me/personal`.
 *
 * Derived from the backend model, so `emergency_contact` is correctly an object
 * (`{ name, phone, ... }`) or null - not a string. Every field is optional
 * because the endpoint upserts a partial personal-info record.
 */
export type PersonalInfoPayload = Partial<PersonalInfoDTO>

export const fetchMyProfile = async () => {
  const resp = await api.get('/profiles/me')
  return resp.data
}

export const savePersonalInfo = async (payload: PersonalInfoPayload) => {
  const resp = await api.post('/profiles/me/personal', payload)
  return resp.data
}

export const listProfileVersions = async () => {
  const resp = await api.get('/profiles/me/versions')
  return resp.data
}