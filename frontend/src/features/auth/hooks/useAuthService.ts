import api from '../../../lib/api'

export const fetchProfile = async () => {
  const resp = await api.get('/users/me')
  return resp.data
}
