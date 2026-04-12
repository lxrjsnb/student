<template>
  <div class="bgFX" aria-hidden="true"></div>

  <div class="app-container">
    <main class="page" :class="{ 'page--with-bottom-nav': hasBottomNav }">
      <div v-if="!currentUser && view !== 'adminLogin' && view !== 'adminPanel'" class="login-container">
        <AuthCard
          :loading="authLoading"
          :message="authMessage"
          :message-type="authMessageType"
          :api-base-url="apiBaseUrl"
          :default-username="rememberedUsername"
          @auth="handleAuth"
          @goAdmin="goAdminLogin"
        />
      </div>

      <AdminLogin
        v-if="view === 'adminLogin'"
        :loading="adminLoading"
        :message="adminMessage"
        :message-type="adminMessageType"
        @login="handleAdminLogin"
        @goHome="goHome"
      />

      <SuperAdminDashboard
        v-else-if="view === 'superAdminDashboard'"
        :isSuperAdmin="isSuperAdmin"
        :token="adminToken"
        :role="currentUser?.role || 'user'"
        @logout="adminLogout"
        @goUsers="goAdminPanel"
        @goRecords="goAdminPanel"
        @goOverview="adminGoOverview"
        @goApprove="goAdminApprove"
        @goAdmins="goAdminPanel"
      />

      <AdminPanel
        v-if="view === 'adminPanel'"
        :token="adminToken"
        :role="currentUser?.role || 'user'"
        @logout="adminLogout"
        @goOverview="adminGoOverview"
        @goApprove="goAdminApprove"
        @goDashboard="goSuperAdminDashboard"
      />

      <AdminApply
        v-else-if="view === 'adminApply' && currentUser"
        :user="currentUser"
        @cancel="goHome"
        @success="goHome"
      />

      <AdminApprove
        v-else-if="view === 'adminApprove'"
        :token="adminToken"
        :role="currentUser?.role || 'user'"
      />

      <AdminPunchApproval v-else-if="view === 'adminPunchApproval' && currentUser" :token="adminAuthToken" />

      <AdminActivityUpload v-else-if="view === 'adminActivityUpload' && currentUser" />

      <AdminProfile
        v-else-if="view === 'adminProfile' && currentUser"
        :user="currentUser"
        @logout="adminLogout"
        @goSuperAdmin="goSuperAdminDashboard"
        @openSettings="goSettings"
      />

      <ActivityDetail v-else-if="view === 'activityDetail' && currentUser" :activity="selectedActivity" @back="goActivities" />

      <ActivitiesList v-else-if="view === 'activities' && currentUser" :activities="activities" @open="openActivity" />

      <ProfileView
        v-else-if="view === 'profile' && currentUser"
        :user="currentUser"
        :total-records="records.length"
        :today-count="records.length"
        :latest-record="latestRecord"
        :refreshing="recordsLoading"
        @openHistory="openRecords"
        @openSettings="goSettings"
        @refresh="refreshRecords"
        @logout="logout"
      />

      <SettingsView
        v-else-if="view === 'settings' && currentUser"
        :user="currentUser"
        @back="isAdmin ? goAdminProfile() : goProfile()"
        @updated="applyUserPatch"
      />

      <Overview
        v-else-if="view === 'overview' && currentUser"
        :user="currentUser"
        :records="records"
        :is-admin="isAdmin"
        @goHome="goHome"
      />

      <PunchHome
        v-else-if="view === 'home' && currentUser"
        :user="currentUser"
        :now="now"
        :loading="punchLoading"
        :disabled="punchDisabled"
        :cooldown-remaining="cooldownRemaining"
        :pending-approval="pendingApproval"
        :pending-count="pendingCount"
        :message="punchMessageType === 'success' ? '' : punchMessage"
        :message-type="punchMessageType"
        @punch="punchNow"
        @openHistory="openRecords"
        @openMessages="openPunchMessages"
      />

      <BottomNav v-if="showMainNav" :current="view" @navigate="navigateMain" />
      <AdminNav v-if="showAdminNav" :current="view" @navigate="navigateAdmin" />

      <RecordsModal :open="recordsOpen" :records="calendarRecords" :loading="calendarLoading" @close="recordsOpen = false" />

      <PunchMessagesModal
        :open="messagesOpen"
        :loading="messagesLoading"
        :records="punchMessages"
        :message="messagesTip"
        :message-type="messagesTipType"
        @close="messagesOpen = false"
        @urge="urgeRecord"
      />

      <SuccessQuoteModal
        :open="successOpen"
        :quote="successQuote.text"
        :from="successQuote.from"
        @close="successOpen = false"
      />
    </main>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { API_BASE_URL, adminLogin, login, logout as apiLogout, me, punch, getPunchMessages, getRecords, urgePhoneChangeRequest, urgePunchRecord } from './lib/api'
import AuthCard from './components/AuthCard.vue'
import AdminLogin from './components/AdminLogin.vue'
import AdminPanel from './components/AdminPanel.vue'
import Overview from './components/Overview.vue'
import AdminApply from './components/AdminApply.vue'
import AdminApprove from './components/AdminApprove.vue'
import AdminPunchApproval from './components/AdminPunchApproval.vue'
import AdminActivityUpload from './components/AdminActivityUpload.vue'
import AdminProfile from './components/AdminProfile.vue'
import SuperAdminDashboard from './components/SuperAdminDashboard.vue'
import PunchHome from './components/PunchHome.vue'
import BottomNav from './components/BottomNav.vue'
import AdminNav from './components/AdminNav.vue'
import RecordsModal from './components/RecordsModal.vue'
import PunchMessagesModal from './components/PunchMessagesModal.vue'
import SuccessQuoteModal from './components/SuccessQuoteModal.vue'
import ActivitiesList from './components/ActivitiesList.vue'
import ActivityDetail from './components/ActivityDetail.vue'
import ProfileView from './components/ProfileView.vue'
import SettingsView from './components/SettingsView.vue'
import { ACTIVITIES } from './lib/activities'
import { getNextQuote } from './lib/quotes'

const STORAGE_KEY_USER = 'punch_user'
const STORAGE_KEY_USERNAME = 'punch_username'
const STORAGE_KEY_ADMIN_TOKEN = 'punch_admin_token'

const LOGIN_TTL_MS = 30 * 24 * 60 * 60 * 1000

const apiBaseUrl = API_BASE_URL

const now = ref(new Date())
const nowText = computed(() => now.value.toLocaleString('zh-CN', { hour12: false }))
const currentDate = computed(() => now.value.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }))
const currentTime = computed(() => now.value.toLocaleTimeString('zh-CN', { hour12: false }))

const authMessage = ref('')
const authMessageType = ref('info')
const authLoading = ref(false)
const rememberedUsername = ref(localStorage.getItem(STORAGE_KEY_USERNAME) || '')

const currentUser = ref(loadUserFromStorage())
const view = ref('home')

const pulsePunch = ref(false)

const punchLoading = ref(false)
const punchMessage = ref('')
const punchMessageType = ref('info')
const recordsOpen = ref(false)
const pendingApproval = ref(false)
const pendingApprovalLatest = ref('')
const pendingCount = ref(0)

const messagesOpen = ref(false)
const messagesLoading = ref(false)
const punchMessages = ref([])
const messagesTip = ref('')
const messagesTipType = ref('info')

const successOpen = ref(false)
const successQuote = ref({ text: '', from: '' })

const activities = ref(ACTIVITIES)
const selectedActivityId = ref('')
const selectedActivity = computed(() => activities.value.find((a) => a.id === selectedActivityId.value) || null)

const showMainNav = computed(() => {
  if (!currentUser.value) return false
  if (isAdmin.value) return false
  if (view.value === 'adminLogin' || view.value === 'adminPanel' || view.value === 'superAdminDashboard') return false
  if (view.value === 'adminApprove' || view.value === 'adminApply') return false
  return ['home', 'activities', 'profile'].includes(view.value)
})

const showAdminNav = computed(() => {
  if (!currentUser.value) return false
  if (!isAdmin.value) return false
  if (view.value === 'adminLogin') return false
  return ['adminPunchApproval', 'adminActivityUpload', 'adminProfile'].includes(view.value)
})

const hasBottomNav = computed(() => showMainNav.value || showAdminNav.value)

const records = ref([])
const recordsLoaded = ref(false)
const recordsLoading = ref(false)
const calendarRecords = ref([])
const calendarLoading = ref(false)
const filterStart = ref('')
const filterEnd = ref('')

const adminToken = ref(localStorage.getItem(STORAGE_KEY_ADMIN_TOKEN) || '')
const adminLoading = ref(false)
const adminMessage = ref('')
const adminMessageType = ref('info')

const lastPunchTime = ref(null)
const cooldownRemaining = ref(0)
const userRole = ref('user')

const isAdmin = computed(() => {
  if (currentUser.value?.role) {
    return ['admin', 'super_admin'].includes(currentUser.value.role)
  }
  return false
})

const isSuperAdmin = computed(() => {
  return currentUser.value?.role === 'super_admin'
})

const adminAuthToken = computed(() => adminToken.value || currentUser.value?.sessionToken || '')

const latestRecord = computed(() => records.value[0] || null)

const punchDisabled = computed(() => punchLoading.value || cooldownRemaining.value > 0)

const filteredRecords = computed(() => {
  const start = filterStart.value
  const end = filterEnd.value
  if (!start && !end) return records.value

  const startOk = start ? (r) => r.punchAt >= new Date(start) : () => true
  const endOk = end ? (r) => r.punchAt <= new Date(end + ' 23:59:59') : () => true
  return records.value.filter(r => startOk(r) && endOk(r))
})

const todayRecord = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return records.value.find(r => r.punchAt >= today)
})

function formatDateTime(timeStr) {
  const d = new Date(timeStr)
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

function loadUserFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_USER)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (parsed?.id === undefined || parsed?.id === null) return null
    if (!parsed?.username) return null

    if (parsed._expiresAt && Date.now() > parsed._expiresAt) {
      localStorage.removeItem(STORAGE_KEY_USER)
      return null
    }
    if (!parsed._expiresAt) {
      parsed._expiresAt = Date.now() + LOGIN_TTL_MS
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(parsed))
    }
    return parsed
  } catch {
    return null
  }
}

function goHome() {
  if (isAdmin.value) {
    view.value = 'adminPunchApproval'
    return
  }
  view.value = 'home'
}

function goProfile() {
  view.value = 'profile'
}

function goSettings() {
  view.value = 'settings'
}

function goActivities() {
  view.value = 'activities'
}

function goOverview() {
  view.value = 'overview'
}

function navigateMain(target) {
  if (target === 'home') goHome()
  if (target === 'activities') goActivities()
  if (target === 'profile') goProfile()
}

function openActivity(activityId) {
  selectedActivityId.value = activityId
  view.value = 'activityDetail'
}

function openRecords() {
  recordsOpen.value = true
  if (!recordsLoaded.value && !recordsLoading.value) refreshRecords()
  if (!calendarLoading.value) refreshCalendarRecords()
}

function setFilterStart(value) {
  filterStart.value = value
}

function setFilterEnd(value) {
  filterEnd.value = value
}

function setUser(user, remember) {
  console.log('setUser 被调用，传入的 user:', user)
  console.log('setUser 前，currentUser.value:', currentUser.value)
  currentUser.value = { ...user }
  console.log('setUser 后，currentUser.value:', currentUser.value)
  if (remember) {
    const toStore = { ...user }
    if (!toStore._expiresAt) toStore._expiresAt = Date.now() + LOGIN_TTL_MS
    localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(toStore))
    localStorage.setItem(STORAGE_KEY_USERNAME, toStore.username)
  } else {
    localStorage.removeItem(STORAGE_KEY_USER)
    localStorage.setItem(STORAGE_KEY_USERNAME, user.username)
  }
  rememberedUsername.value = user.username
}

function applyUserPatch(patch) {
  if (!currentUser.value) return
  currentUser.value = { ...currentUser.value, ...patch }
  if (patch?.username) {
    rememberedUsername.value = patch.username
    localStorage.setItem(STORAGE_KEY_USERNAME, patch.username)
  }
  const stored = localStorage.getItem(STORAGE_KEY_USER)
  if (stored) localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(currentUser.value))
}

function logout() {
  if (currentUser.value?.sessionToken) {
    apiLogout({ sessionToken: currentUser.value.sessionToken }).catch(() => {})
  }
  currentUser.value = null
  view.value = 'home'
  records.value = []
  recordsLoaded.value = false
  calendarRecords.value = []
  calendarLoading.value = false
  punchMessage.value = ''
  pendingApproval.value = false
  pendingApprovalLatest.value = ''
  pendingCount.value = 0
  lastPunchTime.value = null
  cooldownRemaining.value = 0
  localStorage.removeItem(STORAGE_KEY_USER)
  adminToken.value = ''
  localStorage.removeItem(STORAGE_KEY_ADMIN_TOKEN)
}

function goAdminLogin() {
  view.value = 'adminLogin'
}

function goAdminPunchApproval() {
  view.value = 'adminPunchApproval'
}

function goAdminActivityUpload() {
  view.value = 'adminActivityUpload'
}

function goAdminProfile() {
  view.value = 'adminProfile'
}

function navigateAdmin(target) {
  if (target === 'adminPunchApproval') goAdminPunchApproval()
  if (target === 'adminActivityUpload') goAdminActivityUpload()
  if (target === 'adminProfile') goAdminProfile()
}

function setInitialViewForRole(role) {
  if (role === 'admin' || role === 'super_admin') {
    view.value = 'adminPunchApproval'
    return
  }
  view.value = 'home'
}

async function handleAuth(payload) {
  authMessage.value = ''
  authMessageType.value = 'info'

  const username = payload.username?.trim()
  const password = payload.password ?? ''
  if (!username || !password) {
    authMessage.value = '用户名和密码不能为空。'
    authMessageType.value = 'error'
    return
  }

  authLoading.value = true
  console.log('开始登录请求')
  try {
    const data = await login({ username, password })
    console.log('登录响应:', data)
    if (data.code === 200) {
      console.log('登录成功，用户数据:', { id: data.user_id, username: data.username, role: data.role })
      
      if (data.role === 'admin' || data.role === 'super_admin') {
        adminToken.value = data.session_token || ''
        if (adminToken.value) localStorage.setItem(STORAGE_KEY_ADMIN_TOKEN, adminToken.value)
      } else {
        adminToken.value = ''
        localStorage.removeItem(STORAGE_KEY_ADMIN_TOKEN)
      }
      
      setUser({
        id: data.user_id,
        nickname: data.nickname || data.username,
        username: data.username,
        studentNo: data.student_no || '',
        phone: data.phone || '',
        department: data.department || '',
        role: data.role,
        sessionToken: data.session_token || '',
        _expiresAt: data.session_expires_at ? new Date(data.session_expires_at).getTime() : Date.now() + LOGIN_TTL_MS
      }, payload.remember)
      setInitialViewForRole(data.role)
      authMessage.value = ''
      authLoading.value = false
      console.log('设置用户后，currentUser:', currentUser.value)
      try {
        await refreshRecords()
      } catch (err) {
        console.error('刷新记录失败:', err)
      }
      return
    }
    authMessage.value = data.msg || '登录失败。'
    authMessageType.value = 'error'
    authLoading.value = false
  } catch (err) {
    console.error('登录请求失败:', err)
    authMessage.value = `请求失败：${err?.message || '未知错误'}。请确认后端已启动：${apiBaseUrl}`
    authMessageType.value = 'error'
    authLoading.value = false
  }
}

async function refreshRecords({ silent = false } = {}) {
  recordsLoading.value = true
  if (!silent) punchMessage.value = ''
  try {
    if (!currentUser.value?.id) {
      recordsLoading.value = false
      return
    }
    const data = await getRecords({
      userId: currentUser.value.id,
      sessionToken: currentUser.value.sessionToken
    })
    if (data.code !== 200) {
      if (!silent) {
        punchMessage.value = data.msg || '同步记录失败。'
        punchMessageType.value = 'error'
      }
    } else {
      records.value = (data.data || []).map((r) => ({
        ...r,
        punch_time_raw: r.punch_time,
        punchAt: new Date(r.punch_time),
        punch_time: formatDateTime(r.punch_time)
      }))

      const pending = data?.pending || {}
      pendingCount.value = Number(pending?.count || 0)
      pendingApproval.value = !isAdmin.value && pendingCount.value > 0
      pendingApprovalLatest.value = pending?.latest_time || ''
    }
  } catch (err) {
    if (!silent) {
      punchMessage.value = `同步记录失败：${err?.message || '未知错误'}`
      punchMessageType.value = 'error'
    }
  } finally {
    recordsLoaded.value = true
    recordsLoading.value = false
  }
}

async function openPunchMessages() {
  if (!currentUser.value?.id || !currentUser.value?.sessionToken) return
  messagesOpen.value = true
  messagesLoading.value = true
  messagesTip.value = ''
  messagesTipType.value = 'info'
  try {
    const data = await getPunchMessages({
      userId: currentUser.value.id,
      sessionToken: currentUser.value.sessionToken,
      limit: 80,
      includePhone: true
    })
    if (data.code === 200) {
      punchMessages.value = data.data || []
    } else {
      messagesTip.value = data.msg || '加载消息失败。'
      messagesTipType.value = 'error'
      punchMessages.value = []
    }
  } catch (err) {
    messagesTip.value = `加载消息失败：${err?.message || '未知错误'}`
    messagesTipType.value = 'error'
    punchMessages.value = []
  } finally {
    messagesLoading.value = false
  }
}

async function refreshCalendarRecords() {
  if (!currentUser.value?.id || !currentUser.value?.sessionToken) return
  calendarLoading.value = true
  try {
    const data = await getPunchMessages({
      userId: currentUser.value.id,
      sessionToken: currentUser.value.sessionToken,
      limit: 200
    })
    if (data.code === 200) {
      calendarRecords.value = (data.data || []).map((r) => ({
        ...r,
        punch_time_raw: r.punch_time,
        punchAt: new Date(r.punch_time),
        punch_time: formatDateTime(r.punch_time)
      }))
    } else {
      calendarRecords.value = []
    }
  } catch {
    calendarRecords.value = []
  } finally {
    calendarLoading.value = false
  }
}

async function urgeRecord(recordId) {
  if (!currentUser.value?.sessionToken) return
  try {
    const row = typeof recordId === 'object' && recordId ? recordId : { id: recordId }
    const idText = String(row?.id || '')
    const isPhone = row?.item_type === 'phone_change' || idText.startsWith('phone:')
    const numericId = Number(idText.split(':').pop())
    const data = isPhone
      ? await urgePhoneChangeRequest({ requestId: numericId, sessionToken: currentUser.value.sessionToken })
      : await urgePunchRecord({ recordId: numericId, sessionToken: currentUser.value.sessionToken })
    if (data.code === 200) {
      punchMessages.value = (punchMessages.value || []).map((r) =>
        String(r?.id) === idText ? { ...r, is_urge: 1 } : r
      )
      messagesTip.value = data.msg || '催办成功'
      messagesTipType.value = 'info'
      setTimeout(() => {
        if (messagesTipType.value === 'info') messagesTip.value = ''
      }, 1200)
      return
    }
    messagesTip.value = data.msg || '催办失败。'
    messagesTipType.value = 'error'
  } catch (err) {
    messagesTip.value = `催办失败：${err?.message || '未知错误'}`
    messagesTipType.value = 'error'
  }
}

async function punchNow() {
  if (!currentUser.value?.id) return
  if (cooldownRemaining.value > 0) return

  punchLoading.value = true
  punchMessage.value = ''
  punchMessageType.value = 'info'
  console.log('开始签到，用户ID:', currentUser.value.id)
  try {
    const data = await punch({
      userId: currentUser.value.id,
      sessionToken: currentUser.value.sessionToken
    })
    console.log('签到响应:', data)
    if (data.code === 200) {
      punchMessage.value = ''
      punchMessageType.value = 'success'
      lastPunchTime.value = new Date()
      cooldownRemaining.value = 10
      punchLoading.value = false
      try {
        await refreshRecords()
      } catch (err) {
        console.error('刷新记录失败:', err)
      }
      pulsePunch.value = true
      setTimeout(() => {
        pulsePunch.value = false
      }, 900)

      successQuote.value = getNextQuote()
      successOpen.value = true
      return
    }
    if (data.code === 429) {
      punchMessage.value = data.msg
      punchMessageType.value = 'warn'
      punchLoading.value = false
      return
    }
    punchMessage.value = data.msg || '打卡失败。'
    punchMessageType.value = 'error'
    punchLoading.value = false
  } catch (err) {
    console.error('签到请求失败:', err)
    punchMessage.value = `打卡失败：${err?.message || '未知错误'}`
    punchMessageType.value = 'error'
    punchLoading.value = false
  }
}

async function handleAdminLogin(payload) {
  adminMessage.value = ''
  adminMessageType.value = 'info'

  const username = payload.username?.trim()
  const password = payload.password ?? ''
  if (!username || !password) {
    adminMessage.value = '用户名和密码不能为空。'
    adminMessageType.value = 'error'
    return
  }

  adminLoading.value = true
  try {
    const data = await adminLogin({ username, password })
    if (data.code === 200) {
      adminToken.value = data.session_token || ''
      if (adminToken.value) localStorage.setItem(STORAGE_KEY_ADMIN_TOKEN, adminToken.value)

      const user = {
        id: data.user_id,
        username: data.username,
        studentNo: data.student_no || '',
        phone: data.phone || '',
        department: data.department || '',
        role: data.role,
        sessionToken: data.session_token || '',
        _expiresAt: data.session_expires_at ? new Date(data.session_expires_at).getTime() : Date.now() + LOGIN_TTL_MS
      }
      currentUser.value = user
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(user))
      setInitialViewForRole(data.role)
      adminMessage.value = ''
      return
    }
    adminMessage.value = data.msg || '管理员账号或密码错误。'
    adminMessageType.value = 'error'
  } catch (err) {
    adminMessage.value = `请求失败：${err?.message || '未知错误'}。请确认后端已启动：${apiBaseUrl}`
    adminMessageType.value = 'error'
  } finally {
    adminLoading.value = false
  }
}

function adminLogout() {
  if (currentUser.value?.sessionToken) {
    apiLogout({ sessionToken: currentUser.value.sessionToken }).catch(() => {})
  }
  adminToken.value = ''
  currentUser.value = null
  view.value = 'home'
  calendarRecords.value = []
  calendarLoading.value = false
  localStorage.removeItem(STORAGE_KEY_ADMIN_TOKEN)
  localStorage.removeItem(STORAGE_KEY_USER)
}

function adminGoOverview() {
  view.value = 'overview'
}

function goAdminApprove() {
  view.value = 'adminApprove'
}

function goAdminPanel() {
  console.log('=== goAdminPanel ===')
  console.log('adminToken.value:', adminToken.value)
  console.log('currentUser.value:', currentUser.value)
  view.value = 'adminPanel'
}

function goSuperAdminDashboard() {
  view.value = 'superAdminDashboard'
}

function goAdminApply() {
  console.log('=== 进入申请管理员页面 ===')
  console.log('currentUser:', currentUser.value)
  console.log('currentUser.id:', currentUser.value?.id)
  console.log('currentUser.username:', currentUser.value?.username)
  console.log('currentUser.role:', currentUser.value?.role)
  view.value = 'adminApply'
}

let timer = null
let cooldownTimer = null
let pendingPollTimer = null
let reloginListener = null

onMounted(() => {
  reloginListener = (event) => {
    const msg = event?.detail?.msg || '登录已过期，请重新登录'
    logout()
    authMessageType.value = 'error'
    authMessage.value = msg
  }
  window.addEventListener('auth:relogin-required', reloginListener)

  timer = setInterval(() => {
    now.value = new Date()
  }, 1000)
  
  cooldownTimer = setInterval(() => {
    if (cooldownRemaining.value > 0) {
      cooldownRemaining.value--
    }
  }, 1000)

  pendingPollTimer = setInterval(() => {
    if (!currentUser.value?.id) return
    if (isAdmin.value) return
    if (!pendingApproval.value) return
    if (recordsLoading.value) return
    refreshRecords({ silent: true }).catch(() => {})
  }, 15000)
  
  if (currentUser.value?.id) refreshRecords()
  if (currentUser.value?.sessionToken) {
    me({ sessionToken: currentUser.value.sessionToken })
      .then((data) => {
        if (data.code === 200) {
          applyUserPatch({
            nickname: data.nickname || data.username,
            username: data.username,
            studentNo: data.student_no || '',
            phone: data.phone || '',
            department: data.department || '',
            role: data.role
          })
          setInitialViewForRole(data.role)
        } else if (data.code === 401) {
          logout()
        }
      })
      .catch(() => {
        // 忽略：后端可能尚未启用 /me 或 user_sessions
      })
  }

  if (currentUser.value?.role) {
    setInitialViewForRole(currentUser.value.role)
  }
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  if (cooldownTimer) clearInterval(cooldownTimer)
  if (pendingPollTimer) clearInterval(pendingPollTimer)
  if (reloginListener) window.removeEventListener('auth:relogin-required', reloginListener)
})
</script>

<style scoped>
.app-container {
  height: 100dvh;
  width: 100%;
  overflow-y: auto;
  overscroll-behavior-y: none;
  -webkit-overflow-scrolling: touch;
}

.page {
  width: 100%;
  display: flex;
  flex-direction: column;
  background: transparent;
}

.page--with-bottom-nav {
  padding-bottom: calc(88px + env(safe-area-inset-bottom, 0px));
}

.top-bar {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.top-bar__left,
.top-bar__center,
.top-bar__right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-text {
  color: white;
  font-size: 16px;
  font-weight: 700;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.user-id {
  font-size: 12px;
  color: #64748b;
  margin: 0;
}

.info-bar {
  display: flex;
  gap: 32px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-icon {
  font-size: 18px;
}

.info-label {
  font-size: 12px;
  color: #64748b;
}

.info-value {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.status-text {
  font-size: 13px;
  color: #22c55e;
  font-weight: 600;
}

.dashboard {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.dashboard__header {
  margin-bottom: 24px;
}

.dashboard__title {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px;
}

.dashboard__subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.dashboard__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

@media (max-width: 1200px) {
  .dashboard__stats {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .dashboard__stats {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon--primary {
  background: rgba(59, 130, 246, 0.1);
}

.stat-icon--success {
  background: rgba(34, 197, 94, 0.1);
}

.stat-icon--warning {
  background: rgba(245, 158, 11, 0.1);
}

.stat-icon--info {
  background: rgba(99, 102, 241, 0.1);
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  margin: 0 0 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.dashboard__main {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

@media (max-width: 1024px) {
  .dashboard__main {
    grid-template-columns: 1fr;
  }
}

.main-section,
.side-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.card-header {
  padding: 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.card-title {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 4px;
}

.card-subtitle {
  font-size: 13px;
  color: #64748b;
  margin: 0;
}

.card-body {
  padding: 20px;
}

.punch-status {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.status-item {
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.status-label {
  font-size: 12px;
  color: #64748b;
  display: block;
  margin-bottom: 8px;
}

.status-value {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.punch-button {
  width: 100%;
  padding: 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.punch-button:hover:not(.punch-button--disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.punch-button--disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.punch-icon {
  font-size: 28px;
}

.punch-text {
  font-size: 18px;
}

.punch-message {
  margin-top: 16px;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  text-align: center;
}

.punch-message--success {
  background: rgba(34, 197, 94, 0.1);
  color: #15803d;
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.punch-message--error {
  background: rgba(239, 68, 68, 0.1);
  color: #b91c1c;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.punch-message--warn {
  background: rgba(245, 158, 11, 0.1);
  color: #b45309;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.notice-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notice-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.notice-item:hover {
  background: #f1f5f9;
}

.notice-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.notice-content {
  flex: 1;
}

.notice-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 4px;
}

.notice-time {
  font-size: 12px;
  color: #64748b;
  margin: 0;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-action {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-action:hover:not(:disabled) {
  background: #f1f5f9;
  border-color: #cbd5e1;
  transform: translateX(4px);
}

.quick-action:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.quick-icon {
  font-size: 20px;
}

.quick-text {
  flex: 1;
}

.data-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.data-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.data-item:hover {
  background: #f1f5f9;
  transform: translateX(4px);
}

.data-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.data-content {
  flex: 1;
}

.data-label {
  font-size: 12px;
  color: #64748b;
  margin: 0 0 4px;
}

.data-value {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: -260px;
    transition: left 0.3s ease;
  }
  
  .sidebar.open {
    left: 0;
  }
  
  .top-bar {
    padding: 8px 16px;
  }
  
  .info-bar {
    display: none;
  }
  
  .dashboard {
    padding: 16px;
  }
}
</style>

<style>
:root {
  --primary: #00a8cc;
  --primary-dark: #008ba8;
  --success: #22c55e;
  --success-bg: rgba(34, 197, 94, 0.1);
  --success-ink: #15803d;
  --danger: #ef4444;
  --danger-bg: rgba(239, 68, 68, 0.1);
  --danger-ink: #b91c1c;
  --warning: #f59e0b;
  --warning-bg: rgba(245, 158, 11, 0.1);
  --warning-ink: #b45309;
  --text: #1e293b;
  --muted: #64748b;
  --border: #e5e7eb;
  --bg: #f8fafc;
  --shadow-soft: 0 2px 8px rgba(0, 0, 0, 0.04);
  --shadow-strong: 0 4px 16px rgba(0, 0, 0, 0.08);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px;
  width: 100%;
}
</style>
