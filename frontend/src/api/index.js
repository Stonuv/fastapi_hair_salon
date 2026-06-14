import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login:    (data) => api.post('/auth/login', data),
  me:       ()     => api.get('/auth/me'),
}

export const mastersApi = {
  getAll:      ()           => api.get('/masters'),
  getById:     (id)         => api.get(`/masters/${id}`),
  getServices: (id)         => api.get(`/masters/${id}/services`),
  getSchedule: (id)         => api.get(`/masters/${id}/schedule`),
  getSlots:    (id, params) => api.get(`/masters/${id}/slots`, { params }),
}

export const servicesApi = {
  getAll: () => api.get('/services'),
}

export const appointmentsApi = {
  create:         (data)              => api.post('/appointments', data),
  getMy:          ()                  => api.get('/appointments/my'),
  cancel:         (id)                => api.post(`/appointments/${id}/cancel`),
  getMasterToday: (masterId, from, to) =>
    api.get(`/appointments/master/${masterId}`, {
      params: { date_from: from, date_to: to }
    }),
}

export default api
