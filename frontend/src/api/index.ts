/**
 * Public entry point for the generated API client.
 *
 * Application code imports from `@/api` (or a relative path to this file), never
 * from `src/api/generated/**` directly - generated output must never be
 * hand-edited, so it is deliberately kept behind this stable facade.
 *
 * What you get:
 * - every generated request/response type (`PersonalInfoDTO`, `UserResponse`,
 *   `LiteracyLevel`, `IntakeResponse`, ...), derived from the backend OpenAPI
 *   schema, so frontend types can no longer drift from backend DTOs;
 * - a typed function per operation (`getCurrentUserProfileApiV1UsersMeGet`);
 * - a TanStack Query v5 hook per operation
 *   (`useGetCurrentUserProfileApiV1UsersMeGet`), plus `*QueryKey` /
 *   `*QueryOptions` factories for custom caching;
 * - the shared Axios instance, so Firebase auth and the 401 refresh-and-retry
 *   interceptor stay in one place.
 *
 * Regenerate with `npm run generate:api` (see docs/api-types.md).
 */

export { default as api } from '../lib/api'
export { customInstance } from './mutator'
export type { MutatorConfig } from './mutator'

// ---- All generated DTO types ----
export * from './generated/model'

// ---- Operations + hooks, per backend tag ----
// Users -> /users, /users/me (consumed by AuthContext).
export * from './generated/endpoints/users/users'
// Profiles -> /profiles/me (dashboard + profile feature modules).
export * from './generated/endpoints/profiles/profiles'
// Report -> /report and the AI explanation endpoints (Phase 1/2/7).
export * from './generated/endpoints/report/report'
// Questionnaires -> templates, sessions, answers (assessment flow).
export * from './generated/endpoints/questionnaires/questionnaires'