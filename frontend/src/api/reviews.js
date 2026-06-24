import client from './client'

export const reviewsApi = {
  create: (data) => client.post('/reviews', data),
  listForMaster: (masterId, params) => client.get(`/reviews/master/${masterId}`, { params }),
  listAll: (params) => client.get('/reviews', { params }),
  moderate: (id, isPublished) => client.patch(`/reviews/${id}/publish`, { is_published: isPublished }),
  remove: (id) => client.delete(`/reviews/${id}`),
}
