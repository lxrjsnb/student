<template>
  <div class="bgFX" aria-hidden="true"></div>

  <AppHeader
    :user="currentUser"
    :now-text="nowText"
    :view="view"
    :disabled="authLoading || !currentUser"
    @logout="logout"
    @goHome="goHome"
    @goProfile="goProfile"
  />

  <main class="page">
    <AuthCard
      v-if="!currentUser"
      :mode="authMode"
      :loading="authLoading"
      :message="authMessage"
      :message-type="authMessageType"
      :api-base-url="apiBaseUrl"
      :default-username="rememberedUsername"
      @switchMode="switchMode"
      @auth="handleAuth"
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

    <div v-else class="dash">
      <section class="card punch" :class="{ 'card--pulse': pulsePunch }">
        <div class="card__head">
          <div>
            <h2 class="card__title">今日打卡</h2>
            <p class="card__sub">按规范：一天一次；如需补卡请联系管理员。</p>
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
            <div class="status__k">今日状态</div>
            <div class="status__v">
              <span v-if="todayRecord" class="tag tag--ok">已打卡</span>
              <span v-else class="tag tag--warn">未打卡</span>
              <span v-if="todayRecord" class="mono status__time">时间：{{ todayRecord.punch_time }}</span>
            </div>
          </div>
        </div>

        <button class="btn btn--primary btn--big" type="button" :disabled="punchDisabled" @click="punchNow">
          {{ punchDisabled ? (todayRecord ? '今日已打卡' : '处理中…') : '立即打卡' }}
        </button>
        <div v-if="punchMessage" class="alert" :class="`alert--${punchMessageType}`">
          {{ punchMessage }}
        </div>

        <div class="tips">
          <div class="tips__k">规范提示</div>
          <ul class="tips__list">
            <li>打卡时间以服务器时间为准。</li>
            <li>建议先同步记录，确认今日是否已打卡。</li>
            <li>如出现网络错误，请确认后端服务已启动且允许跨域。</li>
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
import { API_BASE_URL, getRecords, login, punch, register } from './lib/api'
import { formatDateTime, isSameYmd, ymd } from './lib/time'

const apiBaseUrl = API_BASE_URL

const STORAGE_KEY_USER = 'punch.user'
const STORAGE_KEY_USERNAME = 'punch.username'

const now = ref(new Date())
const nowText = computed(() => formatDateTime(now.value))
let timer = null

const authMode = ref('login') // login | register
const authLoading = ref(false)
const authMessage = ref('')
const authMessageType = ref('info')
const rememberedUsername = ref(localStorage.getItem(STORAGE_KEY_USERNAME) || '')

const currentUser = ref(loadUserFromStorage())
const view = ref('home') // home | profile

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

const todayRecord = computed(() => {
  const today = now.value
  return records.value.find((r) => isSameYmd(r.punchAt, today)) || null
})

const latestRecord = computed(() => records.value[0] || null)

const punchDisabled = computed(() => punchLoading.value || !!todayRecord.value)

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
  currentUser.value = user
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
  localStorage.removeItem(STORAGE_KEY_USER)
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
  try {
    if (payload.mode === 'register') {
      const data = await register({ username, password })
      if (data.code === 200) {
        authMessage.value = '注册成功，请登录。'
        authMessageType.value = 'success'
        authMode.value = 'login'
        return
      }
      authMessage.value = data.msg || '注册失败。'
      authMessageType.value = 'error'
      return
    }

    const data = await login({ username, password })
    if (data.code === 200) {
      setUser({ id: data.user_id, username }, payload.remember)
      authMessage.value = ''
      await refreshRecords()
      return
    }
    authMessage.value = data.msg || '登录失败。'
    authMessageType.value = 'error'
  } catch (err) {
    authMessage.value = `请求失败：${err?.message || '未知错误'}。请确认后端已启动：${apiBaseUrl}`
    authMessageType.value = 'error'
  } finally {
    authLoading.value = false
  }
}

async function refreshRecords() {
  recordsLoading.value = true
  punchMessage.value = ''
  try {
    if (!currentUser.value?.id) return
    const data = await getRecords({ userId: currentUser.value.id })
    if (data.code !== 200) {
      punchMessage.value = data.msg || '同步记录失败。'
      punchMessageType.value = 'error'
      return
    }
    records.value = (data.data || []).map((r) => ({
      ...r,
      punchAt: new Date(r.punch_time),
      punch_time: formatDateTime(r.punch_time)
    }))
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
  if (todayRecord.value) return

  punchLoading.value = true
  punchMessage.value = ''
  punchMessageType.value = 'info'
  try {
    const data = await punch({ userId: currentUser.value.id })
    if (data.code === 200) {
      punchMessage.value = `打卡成功，时间：${data.time}`
      punchMessageType.value = 'success'
      await refreshRecords()
      pulsePunch.value = true
      setTimeout(() => {
        pulsePunch.value = false
      }, 900)
      return
    }
    punchMessage.value = data.msg || '打卡失败。'
    punchMessageType.value = 'error'
  } catch (err) {
    punchMessage.value = `打卡失败：${err?.message || '未知错误'}`
    punchMessageType.value = 'error'
  } finally {
    punchLoading.value = false
  }
}

onMounted(() => {
  timer = setInterval(() => {
    now.value = new Date()
  }, 1000)
  if (currentUser.value?.id) refreshRecords()
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
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
