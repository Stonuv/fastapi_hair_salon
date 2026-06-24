import client from './client'

export const mastersApi = {
  list: (params) => client.get('/masters', { params }),
  getMe: () => client.get('/masters/me'),
  getById: (id) => client.get(`/masters/${id}`),
  update: (id, data) => client.patch(`/masters/${id}`, data),

  getServices: (id) => client.get(`/masters/${id}/services`),
  addService: (id, serviceId, priceOverride) =>
    client.post(`/masters/${id}/services`, null, {
      params: { service_id: serviceId, price_override: priceOverride ?? undefined },
    }),
  removeService: (id, serviceId) => client.delete(`/masters/${id}/services/${serviceId}`),

  getSchedule: (id) => client.get(`/masters/${id}/schedule`),
  setSchedule: (id, data) => client.post(`/masters/${id}/schedule`, data),
  updateSchedule: (id, dayOfWeek, data) =>
    client.patch(`/masters/${id}/schedule/${dayOfWeek}`, data),

  getSlots: (id, serviceId, targetDate) =>
    client.get(`/masters/${id}/slots`, { params: { service_id: serviceId, target_date: targetDate } }),
}
