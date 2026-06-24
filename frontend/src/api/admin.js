import client from './client'

export const adminApi = {
  getStats: () => client.get('/admin/stats'),

  listUsers: (params) => client.get('/admin/users', { params }),
  changeUserRole: (userId, role) => client.patch(`/admin/users/${userId}/role`, { role }),
  createMasterProfile: (userId) => client.post(`/admin/users/${userId}/master`),
  deleteUser: (userId) => client.delete(`/admin/users/${userId}`),

  deleteService: (serviceId) => client.delete(`/admin/services/${serviceId}`),

  updateMasterPhoto: (masterId, photoUrl) =>
    client.patch(`/admin/masters/${masterId}/photo`, null, { params: { photo_url: photoUrl } }),
}
