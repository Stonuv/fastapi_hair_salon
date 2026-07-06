import client from './client'

export const authApi = {
  register: (data) => client.post('/auth/register', data),
  login:     (data) => client.post('/auth/login', data),
  logout:    ()     => client.post('/auth/logout'),
  me:        ()     => client.get('/auth/me'),
  updateMe:  (data) => client.patch('/auth/me', data),
  requestPasswordReset: (email) => client.post('/auth/password-reset/request', { email }),
  confirmPasswordReset: (token, newPassword) =>
    client.post('/auth/password-reset/confirm', { token, new_password: newPassword }),
}
