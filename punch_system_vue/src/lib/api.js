import axios from 'axios'

export const API_BASE_URL =
  import.meta.env?.VITE_API_BASE_URL?.trim() || 'http://127.0.0.1:5000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  validateStatus: (status) => status >= 200 && status < 300 || status === 401 || status === 429 || status === 400
})

export const adminApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  validateStatus: (status) => status >= 200 && status < 300 || status === 401 || status === 429 || status === 400
})

export async function login({ username, password }) {
  const res = await api.post('/login', { username, password })
  return res.data
}

export async function register({ username, password }) {
  const res = await api.post('/register', { username, password })
  return res.data
}

export async function punch({ userId }) {
  const res = await api.post('/punch', { user_id: userId })
  return res.data
}

export async function getRecords({ userId }) {
  const res = await api.get(`/records/${userId}`)
  return res.data
}

export async function adminLogin({ username, password }) {
  const res = await api.post('/admin/login', { username, password })
  return res.data
}

export async function getAllUsers({ token, role }) {
  console.log('=== getAllUsers ===')
  console.log('token:', token)
  console.log('role:', role)
  const headers = { Authorization: `Bearer ${token}`, 'X-User-Role': role || 'user' }
  console.log('headers:', headers)
  const res = await adminApi.get('/admin/users', {
    headers: headers
  })
  console.log('getAllUsers response:', res.data)
  return res.data
}

export async function getAllRecords({ token, role }) {
  const res = await adminApi.get('/admin/records', {
    headers: { Authorization: `Bearer ${token}`, 'X-User-Role': role || 'user' }
  })
  return res.data
}

export async function deleteRecord({ token, recordId, role }) {
  const res = await adminApi.delete(`/admin/records/${recordId}`, {
    headers: { Authorization: `Bearer ${token}`, 'X-User-Role': role || 'user' }
  })
  return res.data
}

export async function updateUserScore({ token, userId, score, role }) {
  const res = await adminApi.put(`/admin/users/${userId}/score`, { score }, {
    headers: { Authorization: `Bearer ${token}`, 'X-User-Role': role || 'user' }
  })
  return res.data
}

export async function applyForAdmin(data) {
  const res = await api.post('/admin/apply', data)
  return res.data
}

export async function getAdminApplications({ token, role }) {
  const res = await adminApi.get('/admin/applications', {
    headers: { Authorization: `Bearer ${token}`, 'X-User-Role': role || 'user' }
  })
  return res.data
}

export async function approveAdminApplication({ token, applicationId, action, role }) {
  const res = await adminApi.post('/admin/approve', { application_id: applicationId, action }, {
    headers: { Authorization: `Bearer ${token}`, 'X-User-Role': role || 'user' }
  })
  return res.data
}

export async function getUserRole({ userId }) {
  const res = await api.get(`/user/role/${userId}`)
  return res.data
}
