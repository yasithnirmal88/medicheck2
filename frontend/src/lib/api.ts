import axios from 'axios'
import { getAuth } from 'firebase/auth'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// attach firebase idToken if available
api.interceptors.request.use(async (config) => {
  try {
    const auth = getAuth()
    const user = auth.currentUser
    if (user) {
      const token = await user.getIdToken()
      if (config && config.headers) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
  } catch {
    // ignore - unauthenticated
  }
  return config
})

export default api
