/** API client with JWT interceptors and base URL from env. */
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const api = axios.create({ baseURL: `${API_BASE}/api/v1`, timeout: 30000 })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401) {
      const refresh = localStorage.getItem('refresh_token')
      if (refresh && !err.config._retry) {
        err.config._retry = true
        try {
          const { data } = await axios.post(`${API_BASE}/api/v1/auth/refresh`, { refresh_token: refresh })
          localStorage.setItem('access_token', data.access_token)
          err.config.headers.Authorization = `Bearer ${data.access_token}`
          return api(err.config)
        } catch { localStorage.clear(); window.location.href = '/login' }
      } else { localStorage.clear(); window.location.href = '/login' }
    }
    return Promise.reject(err)
  },
)

export default api
