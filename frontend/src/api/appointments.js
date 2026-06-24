import client from './client'

export const appointmentsApi = {
  create: (data) => client.post('/appointments', data),
  getById: (id) => client.get(`/appointments/${id}`),
  cancel: (id) => client.post(`/appointments/${id}/cancel`),
  updateStatus: (id, statusValue) => client.patch(`/appointments/${id}/status`, { status: statusValue }),

  listMy: (params) => client.get('/appointments/my', { params }),
  listForMaster: (masterId, params) => client.get(`/appointments/master/${masterId}`, { params }),
  listAll: (params) => client.get('/appointments', { params }),
}
