/**
 * API Client Configuration
 * 
 * Centralized Axios instance for making API requests to the backend.
 * Automatically attaches Firebase authentication tokens.
 */

import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { getFirebaseAuth, initializeFirebase } from './firebase'

// API base URL from environment
const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_URL
  const envBaseUrl = import.meta.env.VITE_API_BASE_URL
  
  let baseUrl = ''
  
  if (envUrl) {
    baseUrl = envUrl
  } else if (envBaseUrl) {
    baseUrl = envBaseUrl
  } else if (import.meta.env.PROD) {
    // In production (Vercel), use relative path to the same origin
    baseUrl = '/api/v1'
  } else {
    // Default to local development server
    return 'http://localhost:8000/api/v1'
  }
  
  // Ensure base URL ends with /api/v1
  if (!baseUrl.endsWith('/api/v1')) {
    if (baseUrl.endsWith('/')) {
      baseUrl = baseUrl + 'api/v1'
    } else {
      baseUrl = baseUrl + '/api/v1'
    }
  }
  
  return baseUrl
}

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - attach Firebase ID token
api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig): Promise<InternalAxiosRequestConfig> => {
    try {
      // Initialize Firebase if not already done
      try {
        initializeFirebase()
      } catch {
        // Firebase already initialized or not configured
      }

      const auth = getFirebaseAuth()
      const user = auth?.currentUser

      if (user) {
        // Get fresh token
        const token = await user.getIdToken(false) // Don't force refresh for every request
        
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`
        }
      }
    } catch (error) {
      // Log error in development
      if (import.meta.env.DEV) {
        console.warn('Failed to attach Firebase token:', error)
      }
      // Don't fail the request - allow unauthenticated access
    }

    return config
  },
  (error: AxiosError): Promise<never> => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle common errors
api.interceptors.response.use(
  (response: AxiosResponse): AxiosResponse => {
    return response
  },
  async (error: AxiosError): Promise<unknown> => {
    // Handle 401 Unauthorized - token may have expired. Refresh once and retry
    // the original request. A _refreshed flag on the config prevents infinite
    // re-entry: if the retried request still 401s, reject instead of looping.
    if (error.response?.status === 401 && error.config && !(error.config as InternalAxiosRequestConfig & { _refreshed?: boolean })._refreshed) {
      try {
        const auth = getFirebaseAuth()
        const user = auth?.currentUser

        if (user) {
          // Force refresh token and retry once
          const token = await user.getIdToken(true)

          if (token && error.config) {
            error.config.headers.Authorization = `Bearer ${token}`
            ;(error.config as InternalAxiosRequestConfig & { _refreshed?: boolean })._refreshed = true
            return axios(error.config)
          }
        }
      } catch {
        // Token refresh failed - user needs to re-authenticate
        console.error('Token refresh failed')
      }
    }

    // Handle network errors
    if (!error.response) {
      console.error('Network error:', error.message)
    }

    return Promise.reject(error)
  }
)

// API methods for common operations
export const apiClient = {
  get: <T = unknown>(url: string, config?: InternalAxiosRequestConfig): Promise<AxiosResponse<T>> =>
    api.get<T>(url, config),

  post: <T = unknown>(url: string, data?: unknown, config?: InternalAxiosRequestConfig): Promise<AxiosResponse<T>> =>
    api.post<T>(url, data, config),

  put: <T = unknown>(url: string, data?: unknown, config?: InternalAxiosRequestConfig): Promise<AxiosResponse<T>> =>
    api.put<T>(url, data, config),

  patch: <T = unknown>(url: string, data?: unknown, config?: InternalAxiosRequestConfig): Promise<AxiosResponse<T>> =>
    api.patch<T>(url, data, config),

  delete: <T = unknown>(url: string, config?: InternalAxiosRequestConfig): Promise<AxiosResponse<T>> =>
    api.delete<T>(url, config),
}

export default api
