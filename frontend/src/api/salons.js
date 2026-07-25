import client from './client'

export const salonsApi = {
  // Без пагинации — у сети физически десятки точек максимум (ROADMAP.md §4.8).
  // Закрытые точки отдаются только admin/owner, остальным — молча отфильтрованы.
  list: (params) => client.get('/salons', { params }),
  getById: (id) => client.get(`/salons/${id}`),
  create: (data) => client.post('/salons', data),
  update: (id, data) => client.patch(`/salons/${id}`, data),
}
