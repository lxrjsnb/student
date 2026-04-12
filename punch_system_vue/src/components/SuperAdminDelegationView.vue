<template>
  <section class="page">
    <header class="hero">
      <div class="heroHead">
        <button class="backBtn" type="button" @click="$emit('back')">‹</button>
        <div class="heroTitleWrap">
          <div>
          <p class="eyebrow">Delegation</p>
          <h2 class="title">{{ isBaseSuperAdmin ? '放权' : '权限申请' }}</h2>
          </div>
          <button class="quick-btn" type="button" aria-label="申请记录" title="申请记录" @click="recordsOpen = !recordsOpen">
            <ClockIcon />
          </button>
        </div>
      </div>
      <p class="subtitle">{{ isBaseSuperAdmin ? '管理临时主席权限与申请。' : '填写理由后提交给主席审批。' }}</p>
    </header>

    <section v-if="isBaseAdmin && !isTemporaryGranted" class="panel">
      <div class="panelHead">
        <div>
          <p class="panelKicker">Apply</p>
          <h3 class="panelTitle">权限申请</h3>
        </div>
        <button class="refreshBtn" type="button" :disabled="loading" @click="loadData">
          {{ loading ? '加载中…' : '刷新' }}
        </button>
      </div>

      <div v-if="message" class="notice" :class="`notice--${messageType}`">{{ message }}</div>

      <label class="field">
        <span class="fieldLabel">申请理由</span>
        <textarea
          v-model.trim="applyReason"
          class="fieldTextarea"
          rows="5"
          placeholder="请写明为什么需要该权限"
        ></textarea>
      </label>

      <button class="submitBtn" type="button" :disabled="submitting" @click="submitApplication">
        {{ submitting ? '提交中…' : '提交权限申请' }}
      </button>
    </section>

    <section v-if="isBaseAdmin && isTemporaryGranted" class="panel">
      <div class="panelHead">
        <div>
          <p class="panelKicker">Granted</p>
          <h3 class="panelTitle">当前已放权</h3>
        </div>
      </div>
      <p class="emptyText">你当前已处于放权状态，放权结束前不能再次申请。</p>
      <p v-if="props.user?.grantExpiresAt" class="requestMeta">截止 {{ formatDateTime(props.user.grantExpiresAt) }}</p>
    </section>

    <section v-if="isBaseSuperAdmin" class="panel">
      <div class="panelHead">
        <div>
          <p class="panelKicker">Create</p>
          <h3 class="panelTitle">直接放权</h3>
        </div>
        <button class="refreshBtn" type="button" :disabled="loading" @click="loadData">
          {{ loading ? '加载中…' : '刷新' }}
        </button>
      </div>

      <div v-if="message" class="notice" :class="`notice--${messageType}`">{{ message }}</div>

      <div class="fieldGrid">
        <label class="field">
          <span class="fieldLabel">目标部长</span>
          <select v-model="selectedAdminId" class="fieldControl">
            <option value="">请选择</option>
            <option v-for="item in grantableAdmins" :key="item.id" :value="String(item.id)">
              {{ item.nickname || item.username }}@{{ item.username }}
            </option>
          </select>
        </label>

        <label class="field">
          <span class="fieldLabel">时长（小时）</span>
          <input v-model="durationHours" class="fieldControl" type="number" inputmode="numeric" min="1" max="720" placeholder="例如 24" />
        </label>
      </div>

      <button class="submitBtn" type="button" :disabled="submitting" @click="submitGrant">
        {{ submitting ? '提交中…' : '确认放权' }}
      </button>
    </section>

    <section v-if="isBaseSuperAdmin" class="panel">
      <div class="panelHead">
        <div>
          <p class="panelKicker">Requests</p>
          <h3 class="panelTitle">放权申请</h3>
        </div>
      </div>

      <div v-if="pendingApplications.length" class="requestList">
        <article v-for="item in pendingApplications" :key="item.id" class="requestCard">
          <div class="requestTop">
            <div>
              <p class="requestName">{{ item.nickname || item.username }}</p>
              <p class="requestMeta">{{ item.department || '未设置部门' }} · {{ item.student_no || '未设置学号' }}</p>
            </div>
            <span v-if="item.is_urge === 1" class="urgeBadge">催办</span>
          </div>
          <p class="requestReason">{{ item.reason }}</p>
          <div class="requestControls">
            <label class="field field--compact">
              <span class="fieldLabel">时长（小时）</span>
              <input
                v-model="requestHours[item.id]"
                class="fieldControl"
                type="number"
                inputmode="numeric"
                min="1"
                max="720"
                placeholder="24"
              />
            </label>
            <div class="requestActions">
              <button class="ghostAction" type="button" :disabled="processingId === item.id" @click="rejectApplication(item.id)">驳回</button>
              <button class="primaryAction" type="button" :disabled="processingId === item.id" @click="approveApplication(item.id)">通过</button>
            </div>
          </div>
        </article>
      </div>
      <div v-else class="emptyText">暂无待处理的放权申请</div>
    </section>

    <teleport to="body">
      <div v-if="recordsOpen" class="recordsOverlay" @click="recordsOpen = false">
        <section class="recordsSheet" @click.stop>
          <div class="recordsHead">
            <div>
              <p class="panelKicker">{{ isBaseSuperAdmin ? 'Records' : 'My Requests' }}</p>
              <h3 class="panelTitle">申请记录</h3>
            </div>
            <button class="refreshBtn" type="button" @click="recordsOpen = false">关闭</button>
          </div>

          <div v-if="isBaseSuperAdmin">
            <div v-if="applicationRecords.length" class="requestList">
              <article v-for="item in applicationRecords" :key="`record-${item.id}`" class="requestCard">
                <div class="requestTop">
                  <div>
                    <p class="requestName">{{ item.nickname || item.username }}</p>
                    <p class="requestMeta">{{ item.department || '未设置部门' }} · {{ item.student_no || '未设置学号' }}</p>
                  </div>
                  <span class="statusBadge" :class="`statusBadge--${item.status}`">{{ statusText(item.status) }}</span>
                </div>
                <p class="requestReason">{{ item.reason }}</p>
                <p class="requestMeta">{{ formatDateTime(item.created_at) }}</p>
              </article>
            </div>
            <div v-else class="emptyText">暂无申请记录</div>
          </div>

          <div v-else>
            <div v-if="myApplications.length" class="requestList">
              <article v-for="item in myApplications" :key="`my-${item.id}`" class="requestCard">
                <div class="requestTop">
                  <div>
                    <p class="requestName">权限申请 #{{ item.id }}</p>
                    <p class="requestMeta">{{ formatDateTime(item.created_at) }}</p>
                  </div>
                  <span class="statusBadge" :class="`statusBadge--${item.status}`">{{ statusText(item.status) }}</span>
                </div>
                <p class="requestReason">{{ item.reason }}</p>
                <p v-if="item.status === 'approved' && item.expires_at" class="requestMeta">已放权至 {{ formatDateTime(item.expires_at) }}</p>
              </article>
            </div>
            <div v-else class="emptyText">暂无权限申请</div>
          </div>
        </section>
      </div>
    </teleport>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import ClockIcon from './ClockIcon.vue'
import {
  approveDelegationApplication,
  createDelegationApplication,
  createSuperAdminDelegation,
  getAllUsers,
  getMyDelegationApplications,
  getSuperAdminDelegationApplications,
  getSuperAdminDelegations,
  rejectDelegationApplication,
  revokeSuperAdminDelegation
} from '../lib/api'

const props = defineProps({
  user: { type: Object, default: null },
  token: { type: String, default: '' }
})

const emit = defineEmits(['back', 'changed'])

const loading = ref(false)
const submitting = ref(false)
const processingId = ref(null)
const message = ref('')
const messageType = ref('info')

const applyReason = ref('')
const selectedAdminId = ref('')
const durationHours = ref('24')
const grantableAdmins = ref([])
const activeDelegations = ref([])
const pendingApplications = ref([])
const applicationRecords = ref([])
const myApplications = ref([])
const requestHours = reactive({})
const recordsOpen = ref(false)
let messageTimer = null

const isBaseSuperAdmin = computed(() => props.user?.baseRole === 'super_admin')
const isBaseAdmin = computed(() => props.user?.baseRole === 'admin')
const isTemporaryGranted = computed(() => Boolean(props.user?.isTemporarySuperAdmin))

function setMessage(text, type = 'info') {
  message.value = text
  messageType.value = type
  if (messageTimer) clearTimeout(messageTimer)
  if (text) {
    messageTimer = setTimeout(() => {
      message.value = ''
      messageType.value = 'info'
      messageTimer = null
    }, type === 'error' ? 3200 : 2200)
  }
}

function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

function statusText(status) {
  if (status === 'approved') return '已通过'
  if (status === 'rejected') return '已驳回'
  return '待审批'
}

async function loadData() {
  if (!props.token) return
  loading.value = true
  try {
    if (isBaseSuperAdmin.value) {
      const [usersRes, grantsRes, applicationsRes] = await Promise.all([
        getAllUsers({ token: props.token, role: props.user?.role || 'user' }),
        getSuperAdminDelegations({ token: props.token }),
        getSuperAdminDelegationApplications({ token: props.token, status: 'all' })
      ])

      grantableAdmins.value = usersRes.code === 200 ? (usersRes.data || []).filter((item) => item.role === 'admin') : []
      activeDelegations.value = grantsRes.code === 200 ? (grantsRes.data || []).filter((item) => item.status === 'active') : []
      applicationRecords.value = applicationsRes.code === 200 ? (applicationsRes.data || []) : []
      pendingApplications.value = applicationRecords.value.filter((item) => item.status === 'pending')
      pendingApplications.value.forEach((item) => {
        if (!requestHours[item.id]) requestHours[item.id] = '24'
      })
    } else if (isBaseAdmin.value) {
      const data = await getMyDelegationApplications({ token: props.token })
      myApplications.value = data.code === 200 ? (data.data || []) : []
    }
  } catch (err) {
    setMessage(`加载失败：${err?.message || '未知错误'}`, 'error')
  } finally {
    loading.value = false
  }
}

async function submitApplication() {
  if (!applyReason.value.trim()) {
    setMessage('请填写申请理由', 'error')
    return
  }
  submitting.value = true
  setMessage('')
  try {
    const data = await createDelegationApplication({
      token: props.token,
      reason: applyReason.value,
      username: props.user?.username || ''
    })
    if (data.code === 200) {
      setMessage(data.msg || '申请已提交', 'success')
      applyReason.value = ''
      await loadData()
      emit('changed')
      return
    }
    setMessage(data.msg || '提交失败', 'error')
  } catch (err) {
    setMessage(`提交失败：${err?.message || '未知错误'}`, 'error')
  } finally {
    submitting.value = false
  }
}

async function submitGrant() {
  const targetUserId = Number(selectedAdminId.value || 0)
  const hours = Number(durationHours.value || 0)
  if (!targetUserId) return setMessage('请选择要放权的部长', 'error')
  if (!Number.isInteger(hours) || hours < 1 || hours > 720) return setMessage('时长需为 1 到 720 小时之间的整数', 'error')

  submitting.value = true
  setMessage('')
  try {
    const data = await createSuperAdminDelegation({ token: props.token, targetUserId, durationHours: hours })
    if (data.code === 200) {
      setMessage(data.msg || '放权成功', 'success')
      selectedAdminId.value = ''
      durationHours.value = '24'
      await loadData()
      emit('changed')
      return
    }
    setMessage(data.msg || '放权失败', 'error')
  } catch (err) {
    setMessage(`放权失败：${err?.message || '未知错误'}`, 'error')
  } finally {
    submitting.value = false
  }
}

async function approveApplication(applicationId) {
  const hours = Number(requestHours[applicationId] || 0)
  if (!Number.isInteger(hours) || hours < 1 || hours > 720) {
    setMessage('时长需为 1 到 720 小时之间的整数', 'error')
    return
  }
  processingId.value = applicationId
  setMessage('')
  try {
    const data = await approveDelegationApplication({ token: props.token, applicationId, durationHours: hours })
    if (data.code === 200) {
      setMessage(data.msg || '申请已通过', 'success')
      await loadData()
      emit('changed')
      return
    }
    setMessage(data.msg || '处理失败', 'error')
  } catch (err) {
    setMessage(`处理失败：${err?.message || '未知错误'}`, 'error')
  } finally {
    processingId.value = null
  }
}

async function rejectApplication(applicationId) {
  processingId.value = applicationId
  setMessage('')
  try {
    const data = await rejectDelegationApplication({ token: props.token, applicationId })
    if (data.code === 200) {
      setMessage(data.msg || '申请已驳回', 'success')
      await loadData()
      emit('changed')
      return
    }
    setMessage(data.msg || '处理失败', 'error')
  } catch (err) {
    setMessage(`处理失败：${err?.message || '未知错误'}`, 'error')
  } finally {
    processingId.value = null
  }
}

async function revoke(delegationId) {
  processingId.value = delegationId
  try {
    const data = await revokeSuperAdminDelegation({ token: props.token, delegationId })
    if (data.code === 200) {
      setMessage(data.msg || '已收回权限', 'success')
      await loadData()
      emit('changed')
      return
    }
    setMessage(data.msg || '收回失败', 'error')
  } catch (err) {
    setMessage(`收回失败：${err?.message || '未知错误'}`, 'error')
  } finally {
    processingId.value = null
  }
}

onMounted(() => {
  loadData()
})

onBeforeUnmount(() => {
  if (messageTimer) clearTimeout(messageTimer)
})
</script>

<style scoped>
.page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 32px 18px 120px;
}

.hero,
.panel {
  padding: 22px;
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(24, 33, 47, 0.08);
  box-shadow: 0 20px 48px rgba(20, 29, 41, 0.06);
}

.hero {
  padding: 0;
  background: transparent;
  border: 0;
  box-shadow: none;
}

.panel {
  margin-top: 16px;
}

.heroHead,
.panelHead,
.requestTop {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.heroHead {
  justify-content: flex-start;
}

.heroTitleWrap {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.backBtn,
.refreshBtn,
.submitBtn,
.revokeBtn,
.primaryAction,
.ghostAction {
  border: 0;
  border-radius: 999px;
  font-weight: 800;
}

.quick-btn {
  position: relative;
  width: 28px;
  height: 28px;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  display: inline-grid;
  place-items: center;
  padding: 0;
  color: rgba(24, 59, 77, 0.74);
  transition: transform 0.16s ease, opacity 0.16s ease;
}

.quick-btn:hover {
  transform: translateY(-1px);
  opacity: 0.8;
}

.quick-btn :deep(.icon) {
  width: 20px;
  height: 20px;
}

.backBtn {
  width: 42px;
  height: 42px;
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
  font-size: 24px;
}

.refreshBtn,
.ghostAction {
  min-height: 42px;
  padding: 0 16px;
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
  font-size: 13px;
}

.submitBtn,
.primaryAction {
  margin-top: 16px;
  min-height: 46px;
  background: #b78b4a;
  color: #fffaf0;
  font-size: 14px;
}

.submitBtn {
  width: 100%;
}

.revokeBtn {
  min-height: 38px;
  padding: 0 16px;
  background: rgba(154, 47, 39, 0.1);
  color: #9a2f27;
  font-size: 13px;
}

.eyebrow,
.panelKicker {
  margin: 0;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(24, 59, 77, 0.54);
}

.title,
.panelTitle {
  margin: 8px 0 0;
  color: #152131;
  letter-spacing: -0.05em;
}

.title {
  font-size: clamp(30px, 4vw, 46px);
  line-height: 1;
}

.panelTitle {
  font-size: 28px;
  line-height: 1.04;
}

.subtitle {
  margin: 14px 0 0;
  color: rgba(24, 33, 47, 0.62);
  font-size: 14px;
}

.fieldGrid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.field {
  display: grid;
  gap: 8px;
}

.field--compact {
  min-width: 160px;
}

.fieldLabel {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: rgba(24, 59, 77, 0.58);
}

.fieldControl,
.fieldTextarea {
  width: 100%;
  min-height: 50px;
  border-radius: 16px;
  border: 1px solid rgba(24, 33, 47, 0.08);
  background: rgba(255, 255, 255, 0.82);
  padding: 0 14px;
  box-sizing: border-box;
  font-size: 15px;
  color: #152131;
  outline: none;
}

.fieldTextarea {
  min-height: 132px;
  padding: 14px;
  resize: vertical;
}

.notice {
  margin-top: 16px;
  padding: 12px 14px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 800;
}

.notice--success {
  background: rgba(34, 197, 94, 0.12);
  color: #166534;
}

.notice--error {
  background: rgba(239, 68, 68, 0.12);
  color: #991b1b;
}

.grantList,
.requestList {
  display: grid;
  gap: 10px;
}

.recordsOverlay {
  position: fixed;
  inset: 0;
  z-index: 120;
  display: grid;
  place-items: center;
  padding: 18px;
  background: rgba(15, 23, 42, 0.28);
}

.recordsSheet {
  width: min(720px, 100%);
  max-height: min(82vh, 920px);
  overflow: auto;
  padding: 22px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(24, 33, 47, 0.08);
  box-shadow: 0 30px 80px rgba(20, 29, 41, 0.18);
}

.recordsHead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 16px;
}

.grantItem,
.requestCard {
  padding: 14px;
  border-radius: 18px;
  background: rgba(248, 242, 231, 0.66);
}

.grantItem {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.grantMain {
  min-width: 0;
}

.grantName,
.requestName {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  color: #152131;
}

.grantMeta,
.requestMeta,
.requestReason,
.emptyText {
  margin: 6px 0 0;
  font-size: 13px;
  color: rgba(24, 33, 47, 0.62);
  line-height: 1.6;
}

.requestReason {
  color: rgba(24, 33, 47, 0.82);
}

.requestControls,
.requestActions {
  display: flex;
  align-items: end;
  gap: 10px;
}

.requestControls {
  margin-top: 14px;
  justify-content: space-between;
}

.urgeBadge,
.statusBadge {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
}

.urgeBadge {
  background: rgba(239, 68, 68, 0.14);
  color: #991b1b;
}

.statusBadge--approved {
  background: rgba(34, 197, 94, 0.14);
  color: #166534;
}

.statusBadge--rejected {
  background: rgba(239, 68, 68, 0.14);
  color: #991b1b;
}

.statusBadge--pending {
  background: rgba(245, 158, 11, 0.14);
  color: #b45309;
}

@media (max-width: 768px) {
  .page {
    padding: 20px 14px 120px;
  }

  .hero,
  .panel {
    padding: 18px;
    border-radius: 24px;
  }

  .fieldGrid,
  .requestControls,
  .requestActions,
  .grantItem,
  .requestTop {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: stretch;
  }

  .field--compact {
    min-width: 0;
  }

  .recordsOverlay {
    padding: 0;
    align-items: end;
  }

  .recordsSheet {
    width: 100%;
    max-height: 86vh;
    border-radius: 24px 24px 0 0;
    padding: 18px 16px calc(18px + env(safe-area-inset-bottom, 0px));
  }
}
</style>
