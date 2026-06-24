import client from './client'

export const servicesApi = {
  list: (params) => client.get('/services', { params }),
  getById: (id) => client.get(`/services/${id}`),
  create: (data) => client.post('/services', data),
  update: (id, data) => client.patch(`/services/${id}`, data),
}
