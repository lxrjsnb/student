<template>
  <div class="bgFX" aria-hidden="true"></div>

  <AppHeader
    v-if="view !== 'adminLogin' && view !== 'adminPanel'"
    :user="currentUser"
    :now-text="nowText"
    :view="view"
    :disabled="authLoading || !currentUser"
    @logout="logout"
    @goHome="goHome"
    @goProfile="goProfile"
    @goAdmin="goAdminLogin"
  />

  <main class="page">
    <AuthCard
      v-if="!currentUser && view !== 'adminLogin' && view !== 'adminPanel'"
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

    <AdminLogin
      v-if="view === 'adminLogin'"
      :loading="adminLoading"
      :message="adminMessage"
      :message-type="adminMessageType"
      @login="handleAdminLogin"
      @goHome="goHome"
    />

    <AdminPanel
      v-if="view === 'adminPanel'"
      :token="adminToken"
      @logout="adminLogout"
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

    <div v-else-if="view === 'home' && currentUser" class="dash">
      <section class="card punch" :class="{ 'card--pulse': pulsePunch }">
        <div class="card__head">
          <div>
            <h2 class="card__title">签到打卡</h2>
            <p class="card__sub">每次签到获得0.5分，间隔10秒可再次签到。</p>
          </div>
          <div class="headActions">
            <button class="btn btn--ghost" type="button" :disabled="recordsLoading" @click="refreshRecords">
              {{ recordsLoading ? '刷新中…' : '同步记录' }}
            </button>
            <button class="btn btn--iconGlass" type="button" :disabled="recordsLoading" @click="openRecordsModal">
              <ClockIcon />
              <span>记录</span>
            </button>
          </div>
        </div>

        <div class="status">
          <div class="status__item">
            <div class="status__k">当前账号</div>
            <div class="status__v">{{ currentUser.username }}（ID: {{ currentUser.id }}）</div>
          </div>
          <div class="status__item">
            <div class="status__k">当前分数</div>
            <div class="status__v score">{{ userScore.toFixed(1) }}</div>
          </div>
          <div class="status__item">
            <div class="status__k">今日签到次数</div>
            <div class="status__v">{{ records.length }} 次</div>
          </div>
        </div>

        <button class="btn btn--primary btn--big" type="button" :disabled="punchDisabled" @click="punchNow">
          {{ cooldownRemaining > 0 ? `冷却中 (${cooldownRemaining}s)` : (punchLoading ? '处理中…' : '立即签到') }}
        </button>
        <div v-if="punchMessage" class="alert" :class="`alert--${punchMessageType}`">
          {{ punchMessage }}
        </div>

        <div class="tips">
          <div class="tips__k">签到规则</div>
          <ul class="tips__list">
            <li>每次签到获得0.5分</li>
            <li>签到间隔为10秒</li>
            <li>每日可多次签到，无次数限制</li>
            <li>签到时间以服务器时间为准</li>
          </ul>
        </div>
      </section>

      <section class="card side">
        <div class="side__title">快捷入口</div>
        <div class="side__sub">点击查看弹窗记录，或进入个人页。</div>
        <div class="side__btns">
          <button class="btn btn--primary" type="button" @click="openRecordsModal">查看打卡记录</button>
          <button class="btn btn--ghost" type="button" @click="goProfile">进入个人信息</button>
        </div>
      </section>
    </div>
  </main>

  <ModalShell
    :open="recordsModalOpen"
    title="我的打卡记录"
    subtitle="支持筛选与刷新；点击遮罩或按 ESC 关闭。"
    @close="recordsModalOpen = false"
  >
    <RecordsTable
      :records="filteredRecords"
      :records-loaded="recordsLoaded"
      :loading="recordsLoading"
      :filter-start="filterStart"
      :filter-end="filterEnd"
      @refresh="refreshRecords"
      @update:filterStart="setFilterStart"
      @update:filterEnd="setFilterEnd"
      @clearFilters="clearFilters"
    />
  </ModalShell>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import AppHeader from './components/AppHeader.vue'
import AuthCard from './components/AuthCard.vue'
import ProfileCard from './components/ProfileCard.vue'
import RecordsTable from './components/RecordsTable.vue'
import ModalShell from './components/ModalShell.vue'
import ClockIcon from './components/ClockIcon.vue'
import AdminLogin from './components/AdminLogin.vue'
import AdminPanel from './components/AdminPanel.vue'
import { API_BASE_URL, getRecords, login, punch, register, adminLogin } from './lib/api'
import { formatDateTime, isSameYmd, ymd } from './lib/time'

const apiBaseUrl = API_BASE_URL

const STORAGE_KEY_USER = 'punch.user'
const STORAGE_KEY_USERNAME = 'punch.username'
const STORAGE_KEY_ADMIN_TOKEN = 'punch.admin.token'

const now = ref(new Date())
const nowText = computed(() => formatDateTime(now.value))
let timer = null

const authMode = ref('login') // login | register
const authLoading = ref(false)
const authMessage = ref('')
const authMessageType = ref('info')
const rememberedUsername = ref(localStorage.getItem(STORAGE_KEY_USERNAME) || '')

const currentUser = ref(loadUserFromStorage())
const view = ref('home') // home | profile | adminLogin | adminPanel

const pulsePunch = ref(false)
const recordsModalOpen = ref(false)

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

const latestRecord = computed(() => records.value[0] || null)

const punchDisabled = computed(() => punchLoading.value || cooldownRemaining.value > 0)

const filteredRecords = computed(() => {
  const start = filterStart.value
  const end = filterEnd.value
  const startOk = (d) => (start ? ymd(d) >= start : true)
  const endOk = (d) => (end ? ymd(d) <= end : true)

  return records.value.filter((r) => {
    return startOk(r.punchAt) && endOk(r.punchAt)
  })
})

function loadUserFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_USER)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (!parsed?.id || !parsed?.username) return null
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

function openRecordsModal() {
  if (!currentUser.value) return
  view.value = 'home'
  recordsModalOpen.value = true
  if (!recordsLoaded.value && !recordsLoading.value) refreshRecords()
}

function clearFilters() {
  filterStart.value = ''
  filterEnd.value = ''
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
    userScore.value = user.score
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

function adminLogout() {
  adminToken.value = ''
  view.value = 'home'
  localStorage.removeItem(STORAGE_KEY_ADMIN_TOKEN)
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
      adminToken.value = data.token
      localStorage.setItem(STORAGE_KEY_ADMIN_TOKEN, data.token)
      currentUser.value = null
      localStorage.removeItem(STORAGE_KEY_USER)
      view.value = 'adminPanel'
      adminMessage.value = ''
      return
    }
    adminMessage.value = data.msg || '登录失败。'
    adminMessageType.value = 'error'
  } catch (err) {
    adminMessage.value = `请求失败：${err?.message || '未知错误'}。请确认后端已启动：${apiBaseUrl}`
    adminMessageType.value = 'error'
  } finally {
    adminLoading.value = false
  }
}

function goAdminLogin() {
  currentUser.value = null
  localStorage.removeItem(STORAGE_KEY_USER)
  if (adminToken.value) {
    view.value = 'adminPanel'
  } else {
    view.value = 'adminLogin'
  }
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
      console.log('登录成功，用户数据:', { id: data.user_id, username: data.username, score: data.score })
      adminToken.value = ''
      localStorage.removeItem(STORAGE_KEY_ADMIN_TOKEN)
      setUser({ id: data.user_id, username: data.username, score: data.score }, payload.remember)
      authMessage.value = ''
      authLoading.value = false
      console.log('设置用户后，currentUser:', currentUser.value)
      try {
        await refreshRecords()
      } catch (err) {
        console.error('刷新记录失败:', err)
      }
      setTimeout(() => {
        location.reload()
      }, 300)
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
      userScore.value = data.score
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
      setTimeout(() => {
        location.reload()
      }, 1000)
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
.page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 18px 20px 32px;
}

.dash {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 16px;
  align-items: start;
}

@media (max-width: 980px) {
  .dash {
    grid-template-columns: 1fr;
  }
}

.card {
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(229, 231, 235, 0.9);
  border-radius: 16px;
  box-shadow: var(--shadow-strong);
  backdrop-filter: blur(10px);
  padding: 18px;
}

.card--pulse {
  position: relative;
}

.card--pulse::after {
  content: "";
  position: absolute;
  inset: -2px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.35), rgba(124, 58, 237, 0.3), rgba(6, 182, 212, 0.25));
  filter: blur(12px);
  opacity: 0.65;
  z-index: -1;
  animation: glowPulse 0.9s ease-in-out 1;
}

.card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.card__title {
  margin: 0;
  font-size: 16px;
  letter-spacing: 0.2px;
}

.card__sub {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 12px;
}

.btn {
  border: 1px solid transparent;
  border-radius: 12px;
  padding: 10px 12px;
  font-weight: 800;
  background: var(--primary);
  color: var(--primary-ink);
  transition: transform 0.16s ease, filter 0.16s ease;
}

.btn:hover {
  transform: translateY(-1px);
  filter: saturate(1.1);
}

.btn:active {
  transform: translateY(0);
}

.btn--ghost {
  background: rgba(255, 255, 255, 0.55);
  border-color: rgba(229, 231, 235, 0.9);
  color: var(--text);
}

.btn--ghost:hover {
  border-color: rgba(203, 213, 225, 0.95);
}

.btn--primary {
  background: linear-gradient(135deg, var(--primary), var(--accent), var(--accent2));
  background-size: 200% 200%;
  animation: bgShift 10s ease-in-out infinite;
}

.btn--iconGlass {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.55);
  border-color: rgba(229, 231, 235, 0.9);
  color: var(--text);
}

.headActions {
  display: inline-flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.btn--big {
  width: 100%;
  padding: 14px 14px;
  font-size: 16px;
  border-radius: 14px;
  margin-top: 10px;
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.status {
  display: grid;
  gap: 10px;
  padding: 10px 0 4px;
}

.status__item {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid rgba(229, 231, 235, 0.9);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(10px);
}

.status__k {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

.status__v {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-weight: 800;
}

.status__time {
  font-weight: 600;
  color: var(--muted);
}

.mono {
  font-variant-numeric: tabular-nums;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
    "Liberation Mono", "Courier New", monospace;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 900;
  border: 1px solid transparent;
}

.tag--ok {
  background: var(--success-bg);
  color: var(--success-ink);
  border-color: rgba(6, 95, 70, 0.2);
}

.tag--warn {
  background: var(--warn-bg);
  color: var(--warn-ink);
  border-color: rgba(146, 64, 14, 0.2);
}

.alert {
  margin-top: 12px;
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 13px;
  border: 1px solid transparent;
}

.alert--success {
  background: var(--success-bg);
  color: var(--success-ink);
  border-color: rgba(6, 95, 70, 0.2);
}

.alert--error {
  background: var(--danger-bg);
  color: var(--danger-ink);
  border-color: rgba(153, 27, 27, 0.2);
}

.alert--warn {
  background: var(--warn-bg);
  color: var(--warn-ink);
  border-color: rgba(146, 64, 14, 0.2);
}

.alert--info {
  background: #eff6ff;
  color: #1e40af;
  border-color: rgba(30, 64, 175, 0.2);
}

.tips {
  margin-top: 14px;
  border-top: 1px dashed var(--border);
  padding-top: 12px;
}

.tips__k {
  font-size: 12px;
  color: var(--muted);
  font-weight: 900;
  margin-bottom: 6px;
}

.tips__list {
  margin: 0;
  padding-left: 16px;
  color: #475569;
  font-size: 13px;
  display: grid;
  gap: 6px;
}

.side__title {
  font-weight: 950;
  letter-spacing: 0.2px;
}

.side__sub {
  margin-top: 6px;
  font-size: 12px;
  color: var(--muted);
}

.side__btns {
  margin-top: 12px;
  display: grid;
  gap: 10px;
}
</style>
