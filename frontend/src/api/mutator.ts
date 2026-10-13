/**
 * Orval custom mutator - routes ALL generated API calls through the existing
 * shared Axios instance (`src/lib/api.ts`).
 *
 * Why this exists: the shared instance owns two behaviours we must not lose when
 * switching to generated clients.
 *
 *  1. The request interceptor attaches the Firebase ID token
 *     (`Authorization: Bearer <token>`).
 *  2. The response interceptor refreshes an expired token and retries a request
 *     that failed with 401 exactly once (guarded by a `_refreshed` flag).
 *
 * It also centralises the base URL resolution, so dev (`http://localhost:8000`
 * + `/api/v1`), production (relative `/api/v1`) and staging all keep working
 * exactly as the hand-written services do today.
 *
 * NOTE: this file is hand-written infrastructure, not generated code. Only
 * `src/api/generated/**` is written by Orval.
 */

import type { AxiosRequestConfig, AxiosResponse, Method } from 'axios'

// Alias-free path: Orval bundles this file with a bundler rooted at the frontend
// dir, so '@/' and relative hops out of src/api/ are not resolvable here.
import api from '../lib/api'

/** Shape Orval passes to the mutator for every operation. */
export interface MutatorConfig {
  url: string
  method: Method | Lowercase<Method>
  params?: Record<string, unknown> | undefined
  data?: unknown
  headers?: Record<string, unknown> | undefined
  baseUrl?: string | undefined
  /**
   * Orval passes the react-query `signal` for query operations so an
   * in-flight request is cancelled when the query is unmounted or its key
   * changes. Forwarded to axios so that cancellation actually takes effect.
   */
  signal?: AbortSignal | undefined
}

/**
 * Version prefix baked into the OpenAPI paths (`/api/v1/users`, ...).
 *
 * The shared Axios instance already resolves a `baseURL` that ends in `/api/v1`,
 * so a generated path must NOT repeat it. Passing the raw generated URL through
 * would produce the double-prefix request `/api/v1/api/v1/users` - an exact bug
 * this codebase already hit once in `cmsApi.ts`, so it is stripped centrally
 * here instead of being duplicated across every call site.
 */
const API_VERSION_PREFIX = '/api/v1'

const stripVersionPrefix = (url: string): string => {
  if (url.startsWith(`${API_VERSION_PREFIX}/`)) {
    return url.slice(API_VERSION_PREFIX.length)
  }
  return url === API_VERSION_PREFIX ? '' : url
}

/**
 * Perform a request with the shared Axios instance and unwrap the response body.
 *
 * Orval's react-query hooks type each operation as returning the response body
 * directly, so the `AxiosResponse` envelope is stripped here rather than in
 * every consuming component.
 *
 * @throws AxiosError unchanged, so existing interceptors and error handling keep
 * working and TanStack Query's `retry` logic still sees real HTTP status codes.
 */
export const customInstance = async <T>(config: MutatorConfig): Promise<T> => {
  const { url, method, params, data, headers, signal } = config

  const requestConfig: AxiosRequestConfig = {
    url: stripVersionPrefix(url),
    method: method as Method,
    params: params as Record<string, unknown> | undefined,
    headers: headers as Record<string, string> | undefined,
    // Honour react-query cancellation; axios >=1.4 supports an AbortSignal.
    signal,
  }

  // Only attach a body for methods that can carry one, otherwise axios sends an
  // explicit `undefined` content-length that some servers reject.
  if (data !== undefined && method !== 'get' && method !== 'head') {
    requestConfig.data = data
  }

  const response: AxiosResponse<T> = await api.request<T>(requestConfig)
  return response.data
}

export default customInstance