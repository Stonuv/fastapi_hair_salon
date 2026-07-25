import client from './client'

export const adminApi = {
  // salon_id во всех трёх — owner может сузить до одной точки, admin всегда
  // видит только свою (бэкенд принудит, см. resolve_salon_scope).
  getStats: (params) => client.get('/admin/stats', { params }),

  listUsers: (params) => client.get('/admin/users', { params }),
  createUser: (data) => client.post('/admin/users', data),
  updateUser: (userId, data) => client.patch(`/admin/users/${userId}`, data),
  changeUserRole: (userId, role) => client.patch(`/admin/users/${userId}/role`, { role }),
  // Домашняя точка admin'а. Owner-only; назначается ДО повышения роли до
  // admin — ck_users_admin_requires_salon требует salon_id уже в этот момент.
  assignUserSalon: (userId, salonId) =>
    client.patch(`/admin/users/${userId}/salon`, { salon_id: salonId }),
  setUserBlocked: (userId, isBlocked) =>
    client.patch(`/admin/users/${userId}/block`, { is_blocked: isBlocked }),
  // salonId обязателен, когда вызывает owner (своей точки у него нет);
  // admin может не указывать — уйдёт в его собственную.
  createMasterProfile: (userId, salonId) =>
    client.post(`/admin/users/${userId}/master`, salonId ? { salon_id: salonId } : {}),
  deleteUser: (userId) => client.delete(`/admin/users/${userId}`),

  deleteService: (serviceId) => client.delete(`/admin/services/${serviceId}`),

  updateMasterPhoto: (masterId, photoUrl) =>
    client.patch(`/admin/masters/${masterId}/photo`, { photo_url: photoUrl || null }),

  uploadImage: (file) => {
    const form = new FormData()
    form.append('file', file)
    return client.post('/admin/uploads/image', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  getReport: (params) => client.get('/admin/reports', { params }),
  exportReport: (params) => client.get('/admin/reports/export', { params, responseType: 'blob' }),
}
