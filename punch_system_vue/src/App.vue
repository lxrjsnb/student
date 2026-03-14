<template>
  <div class="bgFX" aria-hidden="true"></div>

  <div class="app-container">
    <main class="page">
      <div v-if="currentUser && view !== 'adminLogin' && view !== 'adminPanel'" class="top-bar">
        <div class="top-bar__left">
          <div class="user-info">
            <div class="user-avatar">
              <span class="avatar-text">{{ currentUser.username.charAt(0).toUpperCase() }}</span>
            </div>
            <div class="user-details">
              <p class="user-name">{{ currentUser.username }}</p>
              <p class="user-id">ID: {{ currentUser.id }}</p>
            </div>
          </div>
        </div>
        <div class="top-bar__center">
          <div class="info-bar">
            <div class="info-item">
              <span class="info-icon">📅</span>
              <span class="info-label">日期</span>
              <span class="info-value">{{ currentDate }}</span>
            </div>
            <div class="info-item">
              <span class="info-icon">⏰</span>
              <span class="info-label">时间</span>
              <span class="info-value">{{ currentTime }}</span>
            </div>
            <div class="info-item">
              <span class="info-icon">🌤️</span>
              <span class="info-label">天气</span>
              <span class="info-value">晴</span>
            </div>
          </div>
        </div>
        <div class="top-bar__right">
          <div class="status-indicator">
            <span class="status-dot status-dot--online"></span>
            <span class="status-text">在线</span>
          </div>
        </div>
      </div>

      <div v-if="!currentUser && view !== 'adminLogin' && view !== 'adminPanel'" class="login-container">
        <div class="login-bgFX" aria-hidden="true"></div>
        <AuthCard
          :mode="authMode"
          :loading="authLoading"
          :message="authMessage"
          :message-type="authMessageType"
          :api-base-url="apiBaseUrl"
          :default-username="rememberedUsername"
          @switchMode="switchMode"
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

      <ProfileCard
        v-else-if="view === 'profile'"
        :user="currentUser"
        :today-record="todayRecord"
        :latest="latestRecord"
        :total="records.length"
        :preview="records.slice(0, 5)"
        :records-loaded="recordsLoaded"
        @goHome="goHome"
        @goRecords="openRecordsModal"
        @logout="logout"
      />

      <Overview
        v-else-if="view === 'overview' && currentUser"
        :user="currentUser"
        :records="records"
        :is-admin="isAdmin"
        @goHome="goHome"
      />

      <div v-else-if="view === 'home' && currentUser" class="dashboard">
        <div class="dashboard__header">
          <h2 class="dashboard__title">工作台</h2>
          <p class="dashboard__subtitle">欢迎使用智慧校园考勤管理系统</p>
        </div>

        <div class="dashboard__stats">
          <div class="stat-card">
            <div class="stat-icon stat-icon--primary">📊</div>
            <div class="stat-content">
              <p class="stat-label">今日签到</p>
              <p class="stat-value">{{ records.length }} 次</p>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon stat-icon--success">⭐</div>
            <div class="stat-content">
              <p class="stat-label">当前积分</p>
              <p class="stat-value">{{ userScore.toFixed(1) }} 分</p>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon stat-icon--warning">📈</div>
            <div class="stat-content">
              <p class="stat-label">本月签到</p>
              <p class="stat-value">{{ records.length }} 次</p>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon stat-icon--info">🎯</div>
            <div class="stat-content">
              <p class="stat-label">连续签到</p>
              <p class="stat-value">{{ records.length > 0 ? 1 : 0 }} 天</p>
            </div>
          </div>
        </div>

        <div class="dashboard__main">
          <div class="main-section">
            <div class="section-card">
              <div class="card-header">
                <h3 class="card-title">📝 考勤签到</h3>
                <p class="card-subtitle">每次签到获得0.5分，间隔10秒可再次签到</p>
              </div>
              <div class="card-body">
                <div class="punch-status">
                  <div class="status-item">
                    <span class="status-label">当前账号</span>
                    <span class="status-value">{{ currentUser.username }}</span>
                  </div>
                  <div class="status-item">
                    <span class="status-label">当前分数</span>
                    <span class="status-value score">{{ userScore.toFixed(1) }}</span>
                  </div>
                  <div class="status-item">
                    <span class="status-label">今日签到</span>
                    <span class="status-value">{{ records.length }} 次</span>
                  </div>
                </div>
                <button class="punch-button" :class="{ 'punch-button--disabled': punchDisabled }" @click="punchNow">
                  <span class="punch-icon">👆</span>
                  <span class="punch-text">
                    {{ cooldownRemaining > 0 ? `冷却中 (${cooldownRemaining}s)` : (punchLoading ? '处理中…' : '立即签到') }}
                  </span>
                </button>
                <div v-if="punchMessage" class="punch-message" :class="`punch-message--${punchMessageType}`">
                  {{ punchMessage }}
                </div>
              </div>
            </div>

            <div class="section-card">
              <div class="card-header">
                <h3 class="card-title">📢 系统公告</h3>
              </div>
              <div class="card-body">
                <div class="notice-list">
                  <div class="notice-item">
                    <div class="notice-icon">📢</div>
                    <div class="notice-content">
                      <p class="notice-title">欢迎使用智慧校园考勤系统</p>
                      <p class="notice-time">2024-01-01</p>
                    </div>
                  </div>
                  <div class="notice-item">
                    <div class="notice-icon">📢</div>
                    <div class="notice-content">
                      <p class="notice-title">签到规则：每次签到获得0.5分</p>
                      <p class="notice-time">2024-01-01</p>
                    </div>
                  </div>
                  <div class="notice-item">
                    <div class="notice-icon">📢</div>
                    <div class="notice-content">
                      <p class="notice-title">系统已升级至v1.0.0版本</p>
                      <p class="notice-time">2024-01-01</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="side-section">
            <div class="section-card">
              <div class="card-header">
                <h3 class="card-title">⚡ 快捷操作</h3>
              </div>
              <div class="card-body">
                <div class="quick-actions">
                  <button class="quick-action" @click="refreshRecords" :disabled="recordsLoading">
                    <span class="quick-icon">🔄</span>
                    <span class="quick-text">{{ recordsLoading ? '刷新中…' : '同步记录' }}</span>
                  </button>
                  <button class="quick-action" @click="openRecordsModal">
                    <span class="quick-icon">📋</span>
                    <span class="quick-text">查看记录</span>
                  </button>
                  <button class="quick-action" @click="goProfile">
                    <span class="quick-icon">👤</span>
                    <span class="quick-text">个人中心</span>
                  </button>
                </div>
              </div>
            </div>

            <div class="section-card">
              <div class="card-header">
                <h3 class="card-title">📊 数据统计</h3>
              </div>
              <div class="card-body">
                <div class="data-list">
                  <div class="data-item">
                    <span class="data-icon">⏰</span>
                    <div class="data-content">
                      <p class="data-label">当前时间</p>
                      <p class="data-value">{{ nowText }}</p>
                    </div>
                  </div>
                  <div class="data-item">
                    <span class="data-icon">📊</span>
                    <div class="data-content">
                      <p class="data-label">签到次数</p>
                      <p class="data-value">{{ records.length }} 次</p>
                    </div>
                  </div>
                  <div class="data-item">
                    <span class="data-icon">⭐</span>
                    <div class="data-content">
                      <p class="data-label">当前分数</p>
                      <p class="data-value">{{ userScore.toFixed(1) }} 分</p>
                    </div>
                  </div>
                  <div class="data-item" v-if="latestRecord">
                    <span class="data-icon">🕐</span>
                    <div class="data-content">
                      <p class="data-label">上次签到</p>
                      <p class="data-value">{{ formatDateTime(latestRecord.punch_time) }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { login, register, punch, getRecords } from './lib/api'
import AuthCard from './components/AuthCard.vue'
import AdminLogin from './components/AdminLogin.vue'
import AdminPanel from './components/AdminPanel.vue'
import ProfileCard from './components/ProfileCard.vue'
import ClockIcon from './components/ClockIcon.vue'
import Overview from './components/Overview.vue'
import AdminApply from './components/AdminApply.vue'
import AdminApprove from './components/AdminApprove.vue'
import SuperAdminDashboard from './components/SuperAdminDashboard.vue'

const STORAGE_KEY_USER = 'punch_user'
const STORAGE_KEY_USERNAME = 'punch_username'
const STORAGE_KEY_ADMIN_TOKEN = 'punch_admin_token'

const apiBaseUrl = import.meta.env?.VITE_API_BASE_URL?.trim() || 'http://127.0.0.1:5000'

const now = ref(new Date())
const nowText = computed(() => now.value.toLocaleString('zh-CN', { hour12: false }))
const currentDate = computed(() => now.value.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }))
const currentTime = computed(() => now.value.toLocaleTimeString('zh-CN', { hour12: false }))

const authMode = ref('login')
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

const records = ref([])
const recordsLoaded = ref(false)
const recordsLoading = ref(false)
const filterStart = ref('')
const filterEnd = ref('')

const adminToken = ref(localStorage.getItem(STORAGE_KEY_ADMIN_TOKEN) || '')
const adminLoading = ref(false)
const adminMessage = ref('')
const adminMessageType = ref('info')

const userScore = ref(0)
const lastPunchTime = ref(null)
const cooldownRemaining = ref(0)
const userRole = ref('user')

const isAdmin = computed(() => {
  if (currentUser.value?.username === 'admin') return true
  if (currentUser.value?.role) {
    return ['admin', 'super_admin'].includes(currentUser.value.role)
  }
  return false
})

const isSuperAdmin = computed(() => {
  return currentUser.value?.username === 'admin' || currentUser.value?.role === 'super_admin'
})

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
    if (!parsed?.id || !parsed?.username) return null
    if (parsed.score !== undefined) {
      userScore.value = parseFloat(parsed.score) || 0
    }
    return parsed
  } catch {
    return null
  }
}

function switchMode(mode) {
  authMode.value = mode
  authMessage.value = ''
  authMessageType.value = 'info'
}

function goHome() {
  view.value = 'home'
}

function goProfile() {
  view.value = 'profile'
}

function goOverview() {
  view.value = 'overview'
}

function openRecordsModal() {
  if (!currentUser.value) return
  view.value = 'home'
  if (!recordsLoaded.value && !recordsLoading.value) refreshRecords()
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
  if (user.score !== undefined) {
    userScore.value = parseFloat(user.score) || 0
  }
  view.value = 'home'
  if (remember) {
    localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(user))
    localStorage.setItem(STORAGE_KEY_USERNAME, user.username)
  } else {
    localStorage.removeItem(STORAGE_KEY_USER)
    localStorage.setItem(STORAGE_KEY_USERNAME, user.username)
  }
  rememberedUsername.value = user.username
}

function logout() {
  currentUser.value = null
  view.value = 'home'
  records.value = []
  recordsLoaded.value = false
  punchMessage.value = ''
  userScore.value = 0
  lastPunchTime.value = null
  cooldownRemaining.value = 0
  localStorage.removeItem(STORAGE_KEY_USER)
}

function goAdminLogin() {
  view.value = 'adminLogin'
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
  if (payload.mode === 'register' && password !== payload.confirmPassword) {
    authMessage.value = '两次输入的密码不一致。'
    authMessageType.value = 'error'
    return
  }

  authLoading.value = true
  console.log('开始登录请求，模式:', payload.mode)
  try {
    if (payload.mode === 'register') {
      const data = await register({ username, password })
      console.log('注册响应:', data)
      if (data.code === 200) {
        authMessage.value = '注册成功，请登录。'
        authMessageType.value = 'success'
        authMode.value = 'login'
        authLoading.value = false
        return
      }
      authMessage.value = data.msg || '注册失败。'
      authMessageType.value = 'error'
      authLoading.value = false
      return
    }

    const data = await login({ username, password })
    console.log('登录响应:', data)
    if (data.code === 200) {
      console.log('登录成功，用户数据:', { id: data.user_id, username: data.username, score: data.score, role: data.role })
      
      if (data.role === 'admin' || data.role === 'super_admin') {
        adminToken.value = 'admin_token'
        localStorage.setItem(STORAGE_KEY_ADMIN_TOKEN, 'admin_token')
      } else {
        adminToken.value = ''
        localStorage.removeItem(STORAGE_KEY_ADMIN_TOKEN)
      }
      
      setUser({ id: data.user_id, username: data.username, score: data.score, role: data.role }, payload.remember)
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

async function refreshRecords() {
  recordsLoading.value = true
  punchMessage.value = ''
  try {
    if (!currentUser.value?.id) {
      recordsLoading.value = false
      return
    }
    const data = await getRecords({ userId: currentUser.value.id })
    if (data.code !== 200) {
      punchMessage.value = data.msg || '同步记录失败。'
      punchMessageType.value = 'error'
    } else {
      records.value = (data.data || []).map((r) => ({
        ...r,
        punchAt: new Date(r.punch_time),
        punch_time: formatDateTime(r.punch_time)
      }))
    }
  } catch (err) {
    punchMessage.value = `同步记录失败：${err?.message || '未知错误'}`
    punchMessageType.value = 'error'
  } finally {
    recordsLoaded.value = true
    recordsLoading.value = false
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
    const data = await punch({ userId: currentUser.value.id })
    console.log('签到响应:', data)
    if (data.code === 200) {
      punchMessage.value = `打卡成功，获得${data.points_gained}分！当前分数：${data.score}`
      punchMessageType.value = 'success'
      userScore.value = parseFloat(data.score) || 0
      lastPunchTime.value = new Date()
      cooldownRemaining.value = 10
      punchLoading.value = false
      console.log('签到成功，分数更新为:', data.score)
      try {
        await refreshRecords()
      } catch (err) {
        console.error('刷新记录失败:', err)
      }
      pulsePunch.value = true
      setTimeout(() => {
        pulsePunch.value = false
      }, 900)
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
    const data = await login({ username, password })
    if (data.code === 200) {
      if (username === 'admin') {
        adminToken.value = 'admin_token'
        localStorage.setItem(STORAGE_KEY_ADMIN_TOKEN, 'admin_token')
        currentUser.value = { id: 0, username: 'admin', score: 0, role: 'super_admin' }
        localStorage.removeItem(STORAGE_KEY_USER)
        view.value = 'superAdminDashboard'
        adminMessage.value = ''
        return
      } else if (data.role === 'admin' || data.role === 'super_admin') {
        adminToken.value = 'admin_token'
        localStorage.setItem(STORAGE_KEY_ADMIN_TOKEN, 'admin_token')
        currentUser.value = { id: data.user_id, username: data.username, score: data.score, role: data.role }
        localStorage.removeItem(STORAGE_KEY_USER)
        view.value = data.role === 'super_admin' ? 'superAdminDashboard' : 'adminPanel'
        adminMessage.value = ''
        return
      }
    }
    adminMessage.value = '管理员账号或密码错误。'
    adminMessageType.value = 'error'
  } catch (err) {
    adminMessage.value = `请求失败：${err?.message || '未知错误'}。请确认后端已启动：${apiBaseUrl}`
    adminMessageType.value = 'error'
  } finally {
    adminLoading.value = false
  }
}

function adminLogout() {
  adminToken.value = ''
  view.value = 'home'
  localStorage.removeItem(STORAGE_KEY_ADMIN_TOKEN)
}

function adminGoOverview() {
  adminToken.value = ''
  currentUser.value = { id: 0, username: 'admin', score: 0, role: 'super_admin' }
  localStorage.removeItem(STORAGE_KEY_ADMIN_TOKEN)
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

onMounted(() => {
  timer = setInterval(() => {
    now.value = new Date()
  }, 1000)
  
  cooldownTimer = setInterval(() => {
    if (cooldownRemaining.value > 0) {
      cooldownRemaining.value--
    }
  }, 1000)
  
  if (currentUser.value?.id) refreshRecords()
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  if (cooldownTimer) clearInterval(cooldownTimer)
})
</script>

<style scoped>
.app-container {
  display: flex;
  min-height: 100vh;
  justify-content: center;
  align-items: center;
}

.page {
  width: 100%;
  max-width: 1200px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: transparent;
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

.status-value.score {
  color: #3b82f6;
  font-size: 22px;
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

.bgFX {
  position: fixed;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  width: 100vw;
  height: 100vh;
  min-width: 100vw;
  min-height: 100vh;
  background: radial-gradient(circle at center, #0a192f 0%, #001233 100%);
  overflow: hidden;
}

.bgFX::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: 
    radial-gradient(circle at 20% 30%, rgba(66, 153, 225, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(66, 153, 225, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 40% 80%, rgba(66, 153, 225, 0.05) 0%, transparent 50%);
  animation: pulse 10s ease-in-out infinite;
}

.bgFX::after {
  content: "";
  position: absolute;
  inset: 0;
  background: 
    linear-gradient(135deg, transparent 20%, rgba(66, 153, 225, 0.05) 20%, rgba(66, 153, 225, 0.05) 25%, transparent 25%, transparent 75%, rgba(66, 153, 225, 0.05) 75%, rgba(66, 153, 225, 0.05) 80%, transparent 80%),
    linear-gradient(45deg, transparent 48%, rgba(66, 153, 225, 0.1) 48%, rgba(66, 153, 225, 0.1) 52%, transparent 52%);
  background-size: 100px 100px, 50px 50px;
  opacity: 0.3;
  animation: gridMove 20s linear infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

@keyframes gridMove {
  0% {
    transform: translate(0, 0);
  }
  100% {
    transform: translate(100px, 100px);
  }
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
  --primary: #3b82f6;
  --primary-dark: #2563eb;
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

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: transparent;
  min-height: 100vh;
  color: var(--text);
}



.login-container {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.login-bgFX {
  position: fixed;
  inset: -80px;
  z-index: -1;
  pointer-events: none;
  width: 100%;
  height: 100%;
  background-color: #111;
  background-image: linear-gradient(
      to top,
      #d2b48c 5%,
      #111 6%,
      #111 7%,
      transparent 7%
    ),
    linear-gradient(to bottom, #111 30%, transparent 80%),
    linear-gradient(to right, #b22222, #871a1a 5%, transparent 5%),
    linear-gradient(
      to right,
      transparent 6%,
      #ff6347 6%,
      #ff3814 9%,
      transparent 9%
    ),
    linear-gradient(
      to right,
      transparent 27%,
      #556b2f 27%,
      #39481f 34%,
      transparent 34%
    ),
    linear-gradient(
      to right,
      transparent 51%,
      #fa8072 51%,
      #f85441 57%,
      transparent 57%
    ),
    linear-gradient(to bottom, #111 35%, transparent 35%),
    linear-gradient(
      to right,
      transparent 42%,
      #008080 42%,
      #004d4d 44%,
      transparent 44%
    ),
    linear-gradient(
      to right,
      transparent 45%,
      #008080 45%,
      #004d4d 47%,
      transparent 47%
    ),
    linear-gradient(
      to right,
      transparent 48%,
      #008080 48%,
      #004d4d 50%,
      transparent 50%
    ),
    linear-gradient(
      to right,
      transparent 87%,
      #789 87%,
      #4f5d6a 91%,
      transparent 91%
    ),
    linear-gradient(to bottom, #111 37.5%, transparent 37.5%),
    linear-gradient(
      to right,
      transparent 14%,
      #bdb76b 14%,
      #989244 20%,
      transparent 20%
    ),
    linear-gradient(to bottom, #111 40%, transparent 40%),
    linear-gradient(
      to right,
      transparent 10%,
      #808000 10%,
      #4d4d00 13%,
      transparent 13%
    ),
    linear-gradient(
      to right,
      transparent 21%,
      #8b4513 21%,
      #5e2f0d 25%,
      transparent 25%
    ),
    linear-gradient(
      to right,
      transparent 58%,
      #8b4513 58%,
      #5e2f0d 64%,
      transparent 64%
    ),
    linear-gradient(
      to right,
      transparent 92%,
      #2f4f4f 92%,
      #1c2f2f 95%,
      transparent 95%
    ),
    linear-gradient(to bottom, #111 48%, transparent 48%),
    linear-gradient(
      to right,
      transparent 96%,
      #2f4f4f 96%,
      #1c2f2f 99%,
      transparent 99%
    ),
    linear-gradient(
      to bottom,
      transparent 68.5%,
      transparent 76%,
      #111 76%,
      #111 77.5%,
      transparent 77.5%,
      transparent 86%,
      #111 86%,
      #111 87.5%,
      transparent 87.5%
    ),
    linear-gradient(
      to right,
      transparent 35%,
      #cd5c5c 35%,
      #bc3a3a 41%,
      transparent 41%
    ),
    linear-gradient(to bottom, #111 68%, transparent 68%),
    linear-gradient(
      to right,
      transparent 78%,
      #bc8f8f 78%,
      #bc8f8f 80%,
      transparent 80%,
      transparent 82%,
      #bc8f8f 82%,
      #bc8f8f 83%,
      transparent 83%
    ),
    linear-gradient(
      to right,
      transparent 66%,
      #a52a2a 66%,
      #7c2020 85%,
      transparent 85%
    );
  background-size: 300px 150px;
  background-position: center bottom;
}

.login-bgFX::before {
  content: "";
  width: 100%;
  height: 100%;
  position: absolute;
  inset: 0;
  background-color: #111;
  background-image: linear-gradient(
      to top,
      #d2b48c 5%,
      #111 6%,
      #111 7%,
      transparent 7%
    ),
    linear-gradient(to bottom, #111 30%, transparent 30%),
    linear-gradient(to right, #b22222, #871a1a 5%, transparent 5%),
    linear-gradient(
      to right,
      transparent 6%,
      #ff6347 6%,
      #ff3814 9%,
      transparent 9%
    ),
    linear-gradient(
      to right,
      transparent 27%,
      #556b2f 27%,
      #39481f 34%,
      transparent 34%
    ),
    linear-gradient(
      to right,
      transparent 51%,
      #fa8072 51%,
      #f85441 57%,
      transparent 57%
    ),
    linear-gradient(to bottom, #111 35%, transparent 35%),
    linear-gradient(
      to right,
      transparent 42%,
      #008080 42%,
      #004d4d 44%,
      transparent 44%
    ),
    linear-gradient(
      to right,
      transparent 45%,
      #008080 45%,
      #004d4d 47%,
      transparent 47%
    ),
    linear-gradient(
      to right,
      transparent 48%,
      #008080 48%,
      #004d4d 50%,
      transparent 50%
    ),
    linear-gradient(
      to right,
      transparent 87%,
      #789 87%,
      #4f5d6a 91%,
      transparent 91%
    ),
    linear-gradient(to bottom, #111 37.5%, transparent 37.5%),
    linear-gradient(
      to right,
      transparent 14%,
      #bdb76b 14%,
      #989244 20%,
      transparent 20%
    ),
    linear-gradient(to bottom, #111 40%, transparent 40%),
    linear-gradient(
      to right,
      transparent 10%,
      #808000 10%,
      #4d4d00 13%,
      transparent 13%
    ),
    linear-gradient(
      to right,
      transparent 21%,
      #8b4513 21%,
      #5e2f0d 25%,
      transparent 25%
    ),
    linear-gradient(
      to right,
      transparent 58%,
      #8b4513 58%,
      #5e2f0d 64%,
      transparent 64%
    ),
    linear-gradient(
      to right,
      transparent 92%,
      #2f4f4f 92%,
      #1c2f2f 95%,
      transparent 95%
    ),
    linear-gradient(to bottom, #111 48%, transparent 48%),
    linear-gradient(
      to right,
      transparent 96%,
      #2f4f4f 96%,
      #1c2f2f 99%,
      transparent 99%
    ),
    linear-gradient(
      to bottom,
      transparent 68.5%,
      transparent 76%,
      #111 76%,
      #111 77.5%,
      transparent 77.5%,
      transparent 86%,
      #111 86%,
      #111 87.5%,
      transparent 87.5%
    ),
    linear-gradient(
      to right,
      transparent 35%,
      #cd5c5c 35%,
      #bc3a3a 41%,
      transparent 41%
    ),
    linear-gradient(to bottom, #111 68%, transparent 68%),
    linear-gradient(
      to right,
      transparent 78%,
      #bc8f8f 78%,
      #bc8f8f 80%,
      transparent 80%,
      transparent 82%,
      #bc8f8f 82%,
      #bc8f8f 83%,
      transparent 83%
    ),
    linear-gradient(
      to right,
      transparent 66%,
      #a52a2a 66%,
      #7c2020 85%,
      transparent 85%
    );
  background-size: 300px 150px;
  background-position: center bottom;
  clip-path: circle(150px at center center);
  animation: flashlight 20s ease infinite;
}

.login-bgFX::after {
  content: "";
  width: 25px;
  height: 10px;
  position: absolute;
  left: calc(50% + 59px);
  bottom: 100px;
  background-repeat: no-repeat;
  background-image: radial-gradient(circle, #fff 50%, transparent 50%),
    radial-gradient(circle, #fff 50%, transparent 50%);
  background-size: 10px 10px;
  background-position:
    left center,
    right center;
  animation: eyes 20s infinite;
}

@keyframes flashlight {
  0% {
    clip-path: circle(150px at -25% 10%);
  }

  38% {
    clip-path: circle(150px at 60% 20%);
  }

  39% {
    opacity: 1;
    clip-path: circle(150px at 60% 86%);
  }

  40% {
    opacity: 0;
    clip-path: circle(150px at 60% 86%);
  }

  41% {
    opacity: 1;
    clip-path: circle(150px at 60% 86%);
  }

  42% {
    opacity: 0;
    clip-path: circle(150px at 60% 86%);
  }

  54% {
    opacity: 0;
    clip-path: circle(150px at 60% 86%);
  }

  55% {
    opacity: 1;
    clip-path: circle(150px at 60% 86%);
  }

  59% {
    opacity: 1;
    clip-path: circle(150px at 60% 86%);
  }

  64% {
    clip-path: circle(150px at 45% 78%);
  }

  68% {
    clip-path: circle(150px at 85% 89%);
  }

  72% {
    clip-path: circle(150px at 60% 86%);
  }

  74% {
    clip-path: circle(150px at 60% 86%);
  }

  100% {
    clip-path: circle(150px at 150% 50%);
  }
}

@keyframes eyes {
  0%,
  38% {
    opacity: 0;
  }

  39%,
  41% {
    opacity: 1;
    transform: scaleY(1);
  }

  40% {
    transform: scaleY(0);
    filter: none;
    background-image: radial-gradient(circle, #fff 50%, transparent 50%),
      radial-gradient(circle, #fff 50%, transparent 50%);
  }

  41% {
    transform: scaleY(1);
    background-image: radial-gradient(circle, #ff0000 50%, transparent 50%),
      radial-gradient(circle, #ff0000 50%, transparent 50%);
    filter: drop-shadow(0 0 4px #ff8686);
  }

  42%,
  100% {
    opacity: 0;
  }
}
</style>
