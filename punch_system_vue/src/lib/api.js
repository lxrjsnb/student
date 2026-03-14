import axios from 'axios'

export const API_BASE_URL =
  import.meta.env?.VITE_API_BASE_URL?.trim() || 'http://127.0.0.1:5000'

const AUTH_RELOGIN_EVENT = 'auth:relogin-required'
let reloginTriggered = false

function _shouldSkip401(url = '') {
  return url.includes('/login') || url.includes('/admin/login') || url.includes('/register')
}

function _maybeTriggerRelogin(res) {
  const status = res?.status
  const url = res?.config?.url || ''
  const code = res?.data?.code

  if (_shouldSkip401(url)) return
  if (!(status === 401 || code === 401)) return
  if (reloginTriggered) return
  reloginTriggered = true

  try {
    window.dispatchEvent(
      new CustomEvent(AUTH_RELOGIN_EVENT, {
        detail: { msg: res?.data?.msg || '登录已过期，请重新登录' }
      })
    )
  } catch {
    // ignore
  }
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  validateStatus: (status) =>
    (status >= 200 && status < 300) || status === 400 || status === 401 || status === 403 || status === 429
})

export const adminApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  validateStatus: (status) =>
    (status >= 200 && status < 300) || status === 400 || status === 401 || status === 403 || status === 429
})

api.interceptors.response.use((res) => {
  _maybeTriggerRelogin(res)
  return res
})

adminApi.interceptors.response.use((res) => {
  _maybeTriggerRelogin(res)
  return res
})

export async function login({ username, password }) {
  const res = await api.post('/login', { username, password })
  return res.data
}

export async function register({ username, password }) {
  const res = await api.post('/register', { username, password })
  return res.data
}

export async function punch({ userId, sessionToken } = {}) {
  const headers = sessionToken ? { Authorization: `Bearer ${sessionToken}` } : undefined
  const res = await api.post('/punch', { user_id: userId }, { headers })
  return res.data
}

export async function getRecords({ userId, sessionToken } = {}) {
  const headers = sessionToken ? { Authorization: `Bearer ${sessionToken}` } : undefined
  const res = await api.get(`/records/${userId}`, { headers })
  return res.data
}

export async function adminLogin({ username, password }) {
  const res = await api.post('/admin/login', { username, password })
  return res.data
}

export async function me({ sessionToken }) {
  const res = await api.get('/me', {
    headers: { Authorization: `Bearer ${sessionToken}` }
  })
  return res.data
}

export async function logout({ sessionToken }) {
  const res = await api.post('/logout', null, {
    headers: { Authorization: `Bearer ${sessionToken}` }
  })
  return res.data
}

export async function getAllUsers({ token, role }) {
  console.log('=== getAllUsers ===')
  console.log('token:', token)
  console.log('role:', role)
  const headers = { Authorization: `Bearer ${token}` }
  console.log('headers:', headers)
  const res = await adminApi.get('/admin/users', {
    headers: headers
  })
  console.log('getAllUsers response:', res.data)
  return res.data
}

export async function getAllRecords({ token, role }) {
  const res = await adminApi.get('/admin/records', {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function deleteRecord({ token, recordId, role }) {
  const res = await adminApi.delete(`/admin/records/${recordId}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function applyForAdmin(data) {
  const res = await api.post('/admin/apply', data)
  return res.data
}

export async function getAdminApplications({ token, role }) {
  const res = await adminApi.get('/admin/applications', {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function approveAdminApplication({ token, applicationId, action, role }) {
  const res = await adminApi.post('/admin/approve', { application_id: applicationId, action }, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function getUserRole({ userId }) {
  const res = await api.get(`/user/role/${userId}`)
  return res.data
}

export async function updateUsername({ userId, password, username }) {
  const res = await api.put(`/user/profile/${userId}`, { password, username })
  return res.data
}

export async function changePassword({ userId, oldPassword, newPassword }) {
  const res = await api.put(`/user/password/${userId}`, { old_password: oldPassword, new_password: newPassword })
  return res.data
}
