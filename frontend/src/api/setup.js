import client from './client'

export const setupApi = {
  status:   ()     => client.get('/setup/status'),
  complete: (data) => client.post('/setup', data),
}
