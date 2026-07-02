import client from './client'

export const adminApi = {
  getStats: () => client.get('/admin/stats'),

  listUsers: (params) => client.get('/admin/users', { params }),
  createUser: (data) => client.post('/admin/users', data),
  updateUser: (userId, data) => client.patch(`/admin/users/${userId}`, data),
  changeUserRole: (userId, role) => client.patch(`/admin/users/${userId}/role`, { role }),
  createMasterProfile: (userId) => client.post(`/admin/users/${userId}/master`),
  deleteUser: (userId) => client.delete(`/admin/users/${userId}`),

  deleteService: (serviceId) => client.delete(`/admin/services/${serviceId}`),

  updateMasterPhoto: (masterId, photoUrl) =>
    client.patch(`/admin/masters/${masterId}/photo`, { photo_url: photoUrl || null }),

  getReport: (params) => client.get('/admin/reports', { params }),
  exportReport: (params) => client.get('/admin/reports/export', { params, responseType: 'blob' }),
}
