import axios from 'axios'

function resolveApiBaseUrl() {
  const envBaseUrl = import.meta.env?.VITE_API_BASE_URL?.trim()
  if (envBaseUrl) return envBaseUrl
  const port = import.meta.env?.VITE_API_PORT?.trim() || '5001'

  if (typeof window !== 'undefined' && window.location?.hostname) {
    const protocol = window.location.protocol || 'http:'
    return `${protocol}//${window.location.hostname}:${port}`
  }

  return `http://127.0.0.1:${port}`
}

export const API_BASE_URL = resolveApiBaseUrl()

const AUTH_RELOGIN_EVENT = 'auth:relogin-required'
let reloginTriggered = false

function _shouldSkip401(url = '') {
  return url.includes('/login') || url.includes('/admin/login') || url.includes('/register')
}

function _maybeTriggerRelogin(res) {
  const status = res?.status
  const url = res?.config?.url || ''
  const code = res?.data?.code
  const msg = String(res?.data?.msg || '')

  if (_shouldSkip401(url)) return
  if (!(status === 401 || code === 401)) return
  if (!msg.includes('需要登录') && !msg.includes('重新登录')) return
  if (reloginTriggered) return
  reloginTriggered = true

  try {
    window.dispatchEvent(
      new CustomEvent(AUTH_RELOGIN_EVENT, {
        detail: { msg: msg || '登录已过期，请重新登录' }
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

export async function login({ studentNo, password }) {
  const res = await api.post('/login', { student_no: studentNo, password })
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

export async function getPunchMessages({ userId, sessionToken, limit, includePhone } = {}) {
  const headers = { Authorization: `Bearer ${sessionToken}` }
  const params = {}
  if (limit) params.limit = limit
  if (includePhone) params.include_phone = 1
  const res = await api.get(`/records/messages/${userId}`, { headers, params })
  return res.data
}

export async function urgePunchRecord({ recordId, sessionToken } = {}) {
  const headers = { Authorization: `Bearer ${sessionToken}` }
  const res = await api.post(`/records/${recordId}/urge`, null, { headers })
  return res.data
}

export async function urgePhoneChangeRequest({ requestId, sessionToken } = {}) {
  const headers = { Authorization: `Bearer ${sessionToken}` }
  const res = await api.post(`/phone-change-requests/${requestId}/urge`, null, { headers })
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

export async function getPunchApprovals({ token, userId, username, startDate, endDate, status, limit, page, pageSize } = {}) {
  const params = {}
  if (userId) params.user_id = userId
  if (username) params.username = username
  if (startDate) params.start_date = startDate
  if (endDate) params.end_date = endDate
  if (status) params.status = status
  if (limit) params.limit = limit
  if (page) params.page = page
  if (pageSize) params.page_size = pageSize

  const res = await adminApi.get('/admin/punch-approvals', {
    headers: { Authorization: `Bearer ${token}` },
    params
  })
  return res.data
}

export async function approvePunchRecords({ token, recordIds } = {}) {
  const res = await adminApi.post(
    '/admin/punch-approvals/approve',
    { record_ids: recordIds },
    { headers: { Authorization: `Bearer ${token}` } }
  )
  return res.data
}

export async function rejectPunchRecords({ token, recordIds } = {}) {
  const res = await adminApi.post(
    '/admin/punch-approvals/reject',
    { record_ids: recordIds },
    { headers: { Authorization: `Bearer ${token}` } }
  )
  return res.data
}

export async function deleteRecord({ token, recordId, role }) {
  const res = await adminApi.delete(`/admin/records/${recordId}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function applyForAdmin({ sessionToken, ...data }) {
  const headers = sessionToken ? { Authorization: `Bearer ${sessionToken}` } : undefined
  const res = await api.post('/admin/apply', data, { headers })
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

export async function getUserRole({ userId, sessionToken }) {
  const headers = sessionToken ? { Authorization: `Bearer ${sessionToken}` } : undefined
  const res = await api.get(`/user/role/${userId}`, { headers })
  return res.data
}

export async function getActivities({ sessionToken }) {
  const headers = sessionToken ? { Authorization: `Bearer ${sessionToken}` } : undefined
  const res = await api.get('/activities', { headers })
  return res.data
}

export async function createActivity({ token, ...payload }) {
  const res = await adminApi.post('/admin/activities', payload, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function getAdminActivities({ token }) {
  const res = await adminApi.get('/admin/activities', {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function getAdminMessages({ token }) {
  const res = await adminApi.get('/admin/messages', {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function approveActivity({ token, activityId }) {
  const res = await adminApi.post(`/admin/activities/${activityId}/approve`, null, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function rejectActivity({ token, activityId }) {
  const res = await adminApi.post(`/admin/activities/${activityId}/reject`, null, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function deleteActivity({ token, activityId }) {
  const res = await adminApi.delete(`/admin/activities/${activityId}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function getSuperAdminDelegations({ token }) {
  const res = await adminApi.get('/super-admin/delegations', {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function createDelegationApplication({ token, reason, username }) {
  const res = await adminApi.post(
    '/delegation-applications',
    { reason, username },
    { headers: { Authorization: `Bearer ${token}` } }
  )
  return res.data
}

export async function getMyDelegationApplications({ token }) {
  const res = await adminApi.get('/delegation-applications/mine', {
    headers: { Authorization: `Bearer ${token}` }
  })
  return res.data
}

export async function urgeDelegationApplication({ token, applicationId }) {
  const res = await adminApi.post(
    `/delegation-applications/${applicationId}/urge`,
    null,
    { headers: { Authorization: `Bearer ${token}` } }
  )
  return res.data
}

export async function getSuperAdminDelegationApplications({ token, status } = {}) {
  const params = {}
  if (status) params.status = status
  const res = await adminApi.get('/super-admin/delegation-applications', {
    headers: { Authorization: `Bearer ${token}` },
    params
  })
  return res.data
}

export async function approveDelegationApplication({ token, applicationId, durationHours }) {
  const res = await adminApi.post(
    `/super-admin/delegation-applications/${applicationId}/approve`,
    { duration_hours: durationHours },
    { headers: { Authorization: `Bearer ${token}` } }
  )
  return res.data
}

export async function rejectDelegationApplication({ token, applicationId }) {
  const res = await adminApi.post(
    `/super-admin/delegation-applications/${applicationId}/reject`,
    null,
    { headers: { Authorization: `Bearer ${token}` } }
  )
  return res.data
}

export async function createSuperAdminDelegation({ token, targetUserId, durationHours }) {
  const res = await adminApi.post(
    '/super-admin/delegations',
    { target_user_id: targetUserId, duration_hours: durationHours },
    { headers: { Authorization: `Bearer ${token}` } }
  )
  return res.data
}

export async function revokeSuperAdminDelegation({ token, delegationId }) {
  const res = await adminApi.post(
    `/super-admin/delegations/${delegationId}/revoke`,
    null,
    { headers: { Authorization: `Bearer ${token}` } }
  )
  return res.data
}

export async function updateUsername({ userId, password, username, sessionToken }) {
  const headers = sessionToken ? { Authorization: `Bearer ${sessionToken}` } : undefined
  const res = await api.put(`/user/profile/${userId}`, { password, username }, { headers })
  return res.data
}

export async function updatePhone({ userId, password, phone, sessionToken }) {
  const headers = sessionToken ? { Authorization: `Bearer ${sessionToken}` } : undefined
  const res = await api.put(`/user/phone/${userId}`, { password, phone }, { headers })
  return res.data
}

export async function changePassword({ userId, oldPassword, newPassword, sessionToken }) {
  const headers = sessionToken ? { Authorization: `Bearer ${sessionToken}` } : undefined
  const res = await api.put(`/user/password/${userId}`, { old_password: oldPassword, new_password: newPassword }, { headers })
  return res.data
}
