<template>
  <section class="page">
    <div class="shell">
      <header class="toolbar" role="region" aria-label="审批筛选与操作">
        <div class="toolbar__title">
          <div>
            <p class="kicker">管理员</p>
            <h2 class="title">打卡审批</h2>
          </div>
          <el-button :loading="loading" @click="loadFirstPage">刷新</el-button>
        </div>

        <div class="toolbar__grid">
          <div class="field field--search">
            <label class="label">搜索</label>
            <el-input v-model="filters.search" clearable placeholder="用户名/昵称/用户ID/记录ID" />
          </div>

          <div class="field">
            <label class="label">用户</label>
            <el-autocomplete
              v-model="filters.userKey"
              clearable
              :fetch-suggestions="fetchUserSuggestions"
              placeholder="例如：12 / 张三 / zhangsan"
              @select="onUserSelected"
            />
          </div>

          <div class="field field--range">
            <label class="label">时间</label>
            <el-date-picker
              v-model="filters.dateRange"
              type="daterange"
              unlink-panels
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </div>
        </div>

        <div class="toolbar__actions">
          <div class="left">
            <label class="chk">
              <input type="checkbox" :checked="allPendingSelected" @change="toggleSelectAllPending" />
              <span>全选当前列表待审批</span>
            </label>
            <span class="muted">已选 {{ selectedIds.size }} 条</span>
            <el-button :disabled="loading" @click="resetFilters">重置</el-button>
          </div>
          <div class="right">
            <el-button
              type="danger"
              :loading="rejecting"
              :disabled="selectedIds.size === 0 || approving"
              @click="rejectSelected"
            >
              批量驳回
            </el-button>
            <el-button
              type="success"
              :loading="approving"
              :disabled="selectedIds.size === 0 || rejecting"
              @click="approveSelected"
            >
              批量通过
            </el-button>
          </div>
        </div>

        <div v-if="message" class="alert" :class="`alert--${messageType}`">{{ message }}</div>
      </header>

      <div class="tableWrap">
        <el-table
          ref="tableRef"
          :data="filteredRows"
          :row-key="(row) => row.id"
          border
          height="100%"
          :empty-text="loading ? '加载中…' : '暂无记录'"
          @selection-change="onSelectionChange"
        >
          <el-table-column type="selection" width="52" :selectable="isRowSelectable" />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag v-if="row.approved === 1" type="success">已审批</el-tag>
              <el-tag v-else-if="row.approved === -1" type="danger">已驳回</el-tag>
              <el-tag v-else type="warning">待审批</el-tag>
            </template>
          </el-table-column>
          <el-table-column
            label="催办"
            prop="is_urge"
            width="90"
            sortable
            :sort-method="(a, b) => Number(a.is_urge || 0) - Number(b.is_urge || 0)"
          >
            <template #default="{ row }">
              <el-tag v-if="row.approved === 0 && row.is_urge === 1" type="danger">催办</el-tag>
              <span v-else class="muted">-</span>
            </template>
          </el-table-column>
          <el-table-column
            label="用户"
            prop="userLabel"
            min-width="180"
            sortable
            :sort-method="(a, b) => String(a.userLabel || '').localeCompare(String(b.userLabel || ''), 'zh-CN')"
          >
            <template #default="{ row }">
              <span class="uName">{{ row.userLabel }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="date" label="日期" width="120" sortable />
          <el-table-column prop="time" label="时间" min-width="220" sortable />
        </el-table>
      </div>

      <div class="more">
        <el-button :loading="loading" :disabled="!hasMore" @click="loadMore">
          {{ hasMore ? '加载更多' : '没有更多了' }}
        </el-button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { approvePunchRecords, getAllUsers, getPunchApprovals, rejectPunchRecords } from '../lib/api'

const props = defineProps({
  token: { type: String, required: true }
})

const loading = ref(false)
const approving = ref(false)
const rejecting = ref(false)
const message = ref('')
const messageType = ref('info')

const filters = ref({
  search: '',
  userKey: '',
  dateRange: [],
})

const records = ref([])
const selectedIds = ref(new Set())
const page = ref(1)
const pageSize = ref(200)
const hasMore = ref(false)
const users = ref([])
const tableRef = ref(null)

function fetchUserSuggestions(queryString, cb) {
  const key = (queryString || '').trim().toLowerCase()
  const list = key
    ? users.value
        .filter((u) => `${u.username} ${u.nickname || ''} #${u.id}`.toLowerCase().includes(key))
        .slice(0, 30)
    : users.value.slice(0, 30)

  cb(
    list.map((u) => ({
      value: `${u.username} (#${u.id})`,
      id: u.id
    }))
  )
}

function onUserSelected(item) {
  if (item?.value) filters.value.userKey = item.value
}

function resetFilters() {
  filters.value = { search: '', userKey: '', dateRange: [] }
  selectedIds.value = new Set()
  tableRef.value?.clearSelection?.()
  loadFirstPage()
}

function _fmtDate(d) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function _dateKeyFromTime(timeStr) {
  const text = String(timeStr || '').trim()
  // MySQL DATETIME: "YYYY-MM-DD HH:mm:ss"
  if (text.length >= 10 && /^\d{4}-\d{2}-\d{2}/.test(text)) return text.slice(0, 10)
  const d = new Date(text)
  if (Number.isNaN(d.getTime())) return ''
  return _fmtDate(d)
}

function _timeText(timeStr) {
  const text = String(timeStr || '').trim()
  // 展示数据库实际值：优先直接显示（仅做轻微格式化）
  if (!text) return ''
  const normalized = text.replace('T', ' ').replace('.000Z', '').replace('Z', '').trim()
  // 若包含日期，时间列只展示 HH:mm:ss（或 HH:mm:ss.xxx）
  const m = normalized.match(/^\d{4}-\d{2}-\d{2}\s+(\d{2}:\d{2}:\d{2}(?:\.\d+)?)\b/)
  if (m?.[1]) return m[1]
  // RFC 1123 / 2822: "Sat, 14 Mar 2026 22:39:04 GMT"
  const rfc = normalized.match(/\b(\d{2}:\d{2}:\d{2})(?:\.\d+)?\b/)
  if (rfc?.[1]) return rfc[1]
  return normalized
}

function parseUserKey(key) {
  const raw = (key || '').trim()
  if (!raw) return { userId: '', username: '' }

  const idMatch = raw.match(/#(\d+)\s*$/)
  if (idMatch?.[1]) return { userId: idMatch[1], username: '' }

  if (/^\d+$/.test(raw)) return { userId: raw, username: '' }

  return { userId: '', username: raw }
}

const rows = computed(() => {
  return (records.value || []).map((r) => {
    const approved = Number(r.approved ?? 0)
    const is_urge = Number(r.is_urge ?? 0)
    const userLabel = (r.username || `用户${r.user_id}`).trim()
    return {
      ...r,
      approved,
      is_urge,
      userLabel,
      date: _dateKeyFromTime(r.punch_time),
      time: _timeText(r.punch_time)
    }
  })
})

const filteredRows = computed(() => {
  const q = (filters.value.search || '').trim().toLowerCase()
  if (!q) return rows.value
  return rows.value.filter((r) => {
    const hay = `${r.userLabel} ${r.user_id} ${r.id}`.toLowerCase()
    return hay.includes(q)
  })
})

const allPendingIds = computed(() => filteredRows.value.filter((r) => r.approved === 0).map((r) => r.id))

const allPendingSelected = computed(() => {
  const pending = allPendingIds.value
  if (pending.length === 0) return false
  for (const id of pending) {
    if (!selectedIds.value.has(id)) return false
  }
  return true
})

function toggleSelectAllPending(e) {
  const checked = e?.target?.checked
  if (!tableRef.value) return

  if (!checked) {
    tableRef.value.clearSelection()
    selectedIds.value = new Set()
    return
  }

  // 只选择当前筛选结果中未审批的行
  for (const row of filteredRows.value) {
    if (Number(row.approved ?? 0) !== 0) continue
    tableRef.value.toggleRowSelection(row, true)
  }
}

function isRowSelectable(row) {
  return Number(row?.approved ?? 0) === 0
}

function onSelectionChange(selection) {
  const next = new Set()
  for (const row of selection || []) next.add(row.id)
  selectedIds.value = next
}

async function load({ append = false } = {}) {
  loading.value = true
  message.value = ''
  try {
    const { userId, username } = parseUserKey(filters.value.userKey)
    const startDate = filters.value.dateRange?.[0] || ''
    const endDate = filters.value.dateRange?.[1] || ''
    const data = await getPunchApprovals({
      token: props.token,
      userId,
      username,
      startDate,
      endDate,
      status: 'pending',
      page: page.value,
      pageSize: pageSize.value
    })
    if (data.code === 200) {
      const next = data.data || []
      const meta = data.meta || {}
      hasMore.value = !!meta.has_more
      records.value = append ? [...records.value, ...next] : next
      if (!append) {
        selectedIds.value = new Set()
        tableRef.value?.clearSelection?.()
      }
    } else {
      message.value = data.msg || '加载失败'
      messageType.value = 'error'
    }
  } catch (err) {
    message.value = `加载失败：${err?.message || '未知错误'}`
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (!hasMore.value || loading.value) return
  page.value += 1
  load({ append: true })
}

function loadFirstPage() {
  page.value = 1
  load()
}

let loadTimer = null
function scheduleLoad() {
  if (loadTimer) clearTimeout(loadTimer)
  loadTimer = setTimeout(() => {
    loadFirstPage()
  }, 350)
}

watch(
  () => filters.value.userKey,
  () => {
    scheduleLoad()
  }
)

watch(
  () => filters.value.dateRange,
  () => {
    scheduleLoad()
  },
  { deep: true }
)

async function approveSelected() {
  if (selectedIds.value.size === 0) return
  if (!confirm(`确定通过 ${selectedIds.value.size} 条打卡记录吗？`)) return

  approving.value = true
  message.value = ''
  try {
    const data = await approvePunchRecords({
      token: props.token,
      recordIds: Array.from(selectedIds.value)
    })
    if (data.code === 200) {
      message.value = `审批成功：已更新 ${data.updated ?? 0} 条`
      messageType.value = 'success'
      page.value = 1
      await load()
    } else {
      message.value = data.msg || '审批失败'
      messageType.value = 'error'
    }
  } catch (err) {
    message.value = `审批失败：${err?.message || '未知错误'}`
    messageType.value = 'error'
  } finally {
    approving.value = false
  }
}

async function rejectSelected() {
  if (selectedIds.value.size === 0) return
  if (!confirm(`确定驳回 ${selectedIds.value.size} 条打卡记录吗？`)) return

  rejecting.value = true
  message.value = ''
  try {
    const data = await rejectPunchRecords({
      token: props.token,
      recordIds: Array.from(selectedIds.value)
    })
    if (data.code === 200) {
      message.value = `驳回成功：已更新 ${data.updated ?? 0} 条`
      messageType.value = 'success'
      page.value = 1
      await load()
    } else {
      message.value = data.msg || '驳回失败'
      messageType.value = 'error'
    }
  } catch (err) {
    message.value = `驳回失败：${err?.message || '未知错误'}`
    messageType.value = 'error'
  } finally {
    rejecting.value = false
  }
}

async function loadUsers() {
  try {
    const data = await getAllUsers({ token: props.token })
    if (data.code === 200) {
      users.value = (data.data || []).filter((u) => !['admin', 'super_admin'].includes(u?.role || ''))
    }
  } catch {
    // ignore
  }
}

loadUsers()
loadFirstPage()
</script>

<style scoped>
.page {
  padding: 0 0 92px;
  width: 100%;
  min-height: 100vh;
}

.shell {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.kicker {
  margin: 0;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.6);
}

.title {
  margin: 4px 0 0;
  font-size: 18px;
  font-weight: 1000;
  letter-spacing: 0.2px;
  color: rgba(15, 23, 42, 0.9);
}

.toolbar {
  position: sticky;
  top: 0;
  z-index: 5;
  background: rgba(255, 255, 255, 0.86);
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  padding: 14px 16px 12px;
}

.toolbar__title {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.toolbar__grid {
  margin-top: 12px;
  display: grid;
  grid-template-columns: 1.2fr 1fr 1.4fr;
  gap: 10px;
}

.field {
  display: grid;
  gap: 6px;
}

.field--range {
  display: grid;
  gap: 6px;
}

.toolbar__actions {
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.label {
  font-size: 12px;
  color: rgba(15, 23, 42, 0.62);
  font-weight: 900;
}

.tableWrap {
  width: 100%;
  flex: 1;
  overflow: auto;
  background: rgba(255, 255, 255, 0.78);
  border-top: 1px solid rgba(15, 23, 42, 0.08);
  min-height: 0;
}

.uName {
  font-weight: 1000;
  color: rgba(15, 23, 42, 0.9);
  margin-right: 10px;
}

.uId {
  color: rgba(15, 23, 42, 0.62);
}

.more {
  display: flex;
  justify-content: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.86);
  border-top: 1px solid rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}

.muted {
  font-size: 12px;
  color: rgba(15, 23, 42, 0.62);
}

.alert {
  padding: 10px 12px;
  border-radius: 14px;
  font-weight: 900;
}

.alert--success {
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.2);
  color: #166534;
}

.alert--error {
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #991b1b;
}

.empty {
  text-align: center;
  color: rgba(15, 23, 42, 0.62);
  font-weight: 900;
}

.chk {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.86);
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}

@media (max-width: 900px) {
  .toolbar__grid {
    grid-template-columns: 1fr;
  }

  .field--range {
    grid-template-columns: 1fr;
  }
}
</style>
