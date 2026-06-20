import api from './index'

const adminApi = {
  // Пользователи
  getUsers:            ()                      => api.get('/admin/users'),
  changeRole:          (userId, role)           => api.patch(`/admin/users/${userId}/role`, { role }),
  createMasterProfile: (userId)                 => api.post(`/admin/users/${userId}/master`),
  deleteUser:          (userId)                 => api.delete(`/admin/users/${userId}`),

  // Услуги
  createService:       (data)                   => api.post('/services', data),
  updateService:       (serviceId, data)        => api.patch(`/admin/services/${serviceId}`, data),
  deleteService:       (serviceId)              => api.delete(`/admin/services/${serviceId}`),

  // Мастера
  updateMasterPhoto:   (masterId, photoUrl)     => api.patch(`/admin/masters/${masterId}/photo`, null, { params: { photo_url: photoUrl } }),
  addServiceToMaster:  (masterId, serviceId, priceOverride) =>
    api.post(`/masters/${masterId}/services`, null, {
      params: { service_id: serviceId, price_override: priceOverride }
    }),
  removeServiceFromMaster: (masterId, serviceId) =>
    api.delete(`/masters/${masterId}/services/${serviceId}`),
}

export default adminApi
