import api from './client'

export interface License {
  id: number
  key: string
  status: 'inactive' | 'active' | 'revoked'
  created_at: string
  updated_at: string
  device?: Device
}

export interface Device {
  id: number
  device_id: string
  activated_at: string
}

export const licenseApi = {
  list: () => api.get<License[]>('/admin/licenses/'),
  get: (id: number) => api.get<License>(`/admin/licenses/${id}/`),
  create: () => api.post<License>('/admin/licenses/'),
  revoke: (id: number) => api.delete(`/admin/licenses/${id}/revoke/`),
}

export const deviceApi = {
  list: () => api.get<Device[]>('/admin/devices/'),
}

export const authApi = {
  login: (username: string, password: string) =>
    api.post('/token/', { username, password }),
}
