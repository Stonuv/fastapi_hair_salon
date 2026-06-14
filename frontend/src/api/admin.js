import api from './index'

const adminApi = {
  changeRole:          (userId, role)    => api.patch(`/admin/users/${userId}/role`, { role }),
  createMasterProfile: (userId)          => api.post(`/admin/users/${userId}/master`),
  createService:       (data)            => api.post('/services', data),
  addServiceToMaster:  (masterId, serviceId, priceOverride) =>
    api.post(`/masters/${masterId}/services`, null, {
      params: { service_id: serviceId, price_override: priceOverride }
    }),
}

export default adminApi
