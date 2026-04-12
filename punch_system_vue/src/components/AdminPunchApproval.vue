<template>
  <section class="page">
    <div class="shell">
      <header class="toolbar" role="region" aria-label="审批筛选与操作">
        <div class="toolbar__title">
          <div>
            <p class="kicker">管理员</p>
            <h2 class="title">审批</h2>
          </div>
          <div class="toolbar__titleActions">
            <el-button :disabled="loading" @click="resetFilters">重置</el-button>
            <el-button :loading="loading" @click="loadFirstPage">刷新</el-button>
          </div>
        </div>

        <div class="toolbar__grid">
          <div class="field field--search">
            <label class="label">搜索</label>
            <el-input v-model="filters.search" clearable placeholder="用户名/昵称/用户ID/记录ID" />
          </div>

          <div class="field field--range">
            <label class="label">时间</label>
            <div class="datePickerGroup">
              <div class="dateInputs">
                <button
                  type="button"
                  class="dateBox"
                  :class="{ 'dateBox--active': pickerState.field === 'startDate' }"
                  @click="toggleDatePicker('startDate')"
                >
                  <span class="dateBox__label">开始日期</span>
                  <span class="dateBox__value">{{ formatDateDisplay(filters.startDate) || '请选择' }}</span>
                </button>
                <button
                  type="button"
                  class="dateBox"
                  :class="{ 'dateBox--active': pickerState.field === 'endDate' }"
                  @click="toggleDatePicker('endDate')"
                >
                  <span class="dateBox__label">结束日期</span>
                  <span class="dateBox__value">{{ formatDateDisplay(filters.endDate) || '请选择' }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
        <div v-if="message" class="alert" :class="`alert--${messageType}`">{{ message }}</div>
      </header>

      <div class="tableWrap">
        <el-table
          class="desktopTable"
          ref="tableRef"
          :data="filteredRows"
          :row-key="(row) => row.id"
          border
          height="100%"
          :empty-text="loading ? '加载中…' : '暂无记录'"
          @selection-change="onSelectionChange"
        >
          <el-table-column type="selection" width="52" :selectable="isRowSelectable" />
          <el-table-column label="类型" width="96">
            <template #default="{ row }">
              <el-tag v-if="row.item_type === 'phone'" type="info">手机号</el-tag>
              <el-tag v-else type="primary">打卡</el-tag>
            </template>
          </el-table-column>
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
          <el-table-column prop="content" label="内容" min-width="180" />
        </el-table>

        <div class="mobileList">
          <div v-if="loading" class="empty">加载中…</div>
          <template v-else-if="filteredRows.length">
            <article v-for="row in filteredRows" :key="row.id" class="mobileCard">
              <div class="mobileCard__top">
                <label v-if="row.approved === 0" class="mobileCheck">
                  <input
                    type="checkbox"
                    :checked="selectedIds.has(row.id)"
                    @change="toggleCardSelection(row.id, $event.target.checked)"
                  />
                  <span>选择</span>
                </label>
                <div v-else class="mobileCheck mobileCheck--ghost">已处理</div>

                <div class="mobileTags">
                  <span class="pill" :class="`pill--${row.item_type}`">{{ row.item_type === 'phone' ? '手机号' : '打卡' }}</span>
                  <span class="pill" :class="`pill--${statusKey(row)}`">{{ statusText(row) }}</span>
                  <span v-if="row.approved === 0 && row.is_urge === 1" class="pill pill--urge">催办</span>
                </div>
              </div>

              <div class="mobileCard__main">
                <h3 class="mobileUser">{{ row.userLabel }}</h3>
                <p class="mobileContent">{{ row.content }}</p>
              </div>

              <dl class="mobileMeta">
                <div class="mobileMeta__item">
                  <dt>日期</dt>
                  <dd>{{ row.date || '-' }}</dd>
                </div>
                <div class="mobileMeta__item">
                  <dt>时间</dt>
                  <dd>{{ row.time || '-' }}</dd>
                </div>
              </dl>
            </article>
          </template>
          <div v-else class="empty">暂无记录</div>
        </div>
      </div>

      <div class="more">
        <el-button :loading="loading" :disabled="!hasMore" @click="loadMore">
          {{ hasMore ? '加载更多' : '没有更多了' }}
        </el-button>
      </div>
    </div>

    <teleport to="body">
      <div v-if="pickerState.field" class="pickerOverlay" @click="closeDatePicker">
        <div class="pickerSheet" @click.stop>
          <div class="pickerSheet__head">
            <div>
              <p class="pickerSheet__eyebrow">
                {{ pickerState.field === 'startDate' ? '开始日期' : '结束日期' }}
              </p>
              <h3 class="pickerSheet__title">选择日期</h3>
            </div>
            <button type="button" class="pickerGhostButton" @click="closeDatePicker">关闭</button>
          </div>

          <p class="pickerSheet__summary">{{ pickerSummary }}</p>

          <div class="pickerColumns">
            <section class="pickerColumn">
              <div class="pickerColumn__head">年</div>
              <div class="pickerList">
                <button
                  v-for="year in pickerYearsDesc"
                  :key="year"
                  type="button"
                  class="pickerItem"
                  :class="{ 'pickerItem--selected': pickerState.year === year }"
                  @click="selectPickerYear(year)"
                >
                  {{ year }}年
                </button>
              </div>
            </section>

            <section class="pickerColumn">
              <div class="pickerColumn__head">月</div>
              <div class="pickerList">
                <button
                  v-for="month in pickerMonths"
                  :key="month"
                  type="button"
                  class="pickerItem"
                  :class="{ 'pickerItem--selected': pickerState.month === month }"
                  @click="selectPickerMonth(month)"
                >
                  {{ month }}月
                </button>
              </div>
            </section>

            <section class="pickerColumn">
              <div class="pickerColumn__head">日</div>
              <div class="pickerList">
                <button
                  v-for="day in pickerDays"
                  :key="day"
                  type="button"
                  class="pickerItem"
                  :class="{ 'pickerItem--selected': pickerState.day === day }"
                  @click="selectPickerDay(day)"
                >
                  {{ day }}日
                </button>
              </div>
            </section>
          </div>

          <div class="pickerSheet__actions">
            <button type="button" class="pickerGhostButton" @click="clearDateField">清空</button>
            <button type="button" class="pickerPrimaryButton" :disabled="!canConfirmDate" @click="applyDatePicker">
              确定
            </button>
          </div>
        </div>
      </div>
    </teleport>

    <transition name="selectionDock">
      <teleport to="body">
        <div v-if="selectedIds.size > 0" class="selectionDock">
          <div class="selectionDock__shell">
            <div class="selectionDock__main">
              <label class="selectionDock__check">
                <input type="checkbox" :checked="allPendingSelected" @change="toggleSelectAllPending" />
                <span>全选当前列表待审批</span>
              </label>
              <p class="selectionDock__count">已选 {{ selectedIds.size }} 条</p>
            </div>

            <div class="selectionDock__actions">
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
        </div>
      </teleport>
    </transition>
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
  startDate: '',
  endDate: '',
})

const records = ref([])
const selectedIds = ref(new Set())
const page = ref(1)
const pageSize = ref(200)
const hasMore = ref(false)
const users = ref([])
const tableRef = ref(null)
const pickerState = ref({
  field: '',
  year: '',
  month: '',
  day: '',
})

function resetFilters() {
  filters.value = { search: '', userKey: '', startDate: '', endDate: '' }
  selectedIds.value = new Set()
  tableRef.value?.clearSelection?.()
  loadFirstPage()
}

function _fmtDate(d) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function pad2(value) {
  return String(value).padStart(2, '0')
}

function splitDateParts(value) {
  const text = String(value || '').trim()
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (!match) return null
  return { year: match[1], month: match[2], day: match[3] }
}

function formatDateDisplay(value) {
  const parts = splitDateParts(value)
  if (!parts) return ''
  return `${parts.year}年${parts.month}月${parts.day}日`
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

const pickerYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 13 }, (_, index) => String(currentYear - 8 + index))
})

const pickerYearsDesc = computed(() => pickerYears.value.slice().reverse())

const pickerMonths = computed(() => Array.from({ length: 12 }, (_, index) => pad2(index + 1)))

const pickerDays = computed(() => {
  const year = Number(pickerState.value.year)
  const month = Number(pickerState.value.month)
  if (!year || !month) return []
  const totalDays = new Date(year, month, 0).getDate()
  return Array.from({ length: totalDays }, (_, index) => pad2(index + 1))
})

const pickerSummary = computed(() => {
  const parts = []
  if (pickerState.value.year) parts.push(`${pickerState.value.year}年`)
  if (pickerState.value.month) parts.push(`${pickerState.value.month}月`)
  if (pickerState.value.day) parts.push(`${pickerState.value.day}日`)
  return parts.length ? parts.join(' ') : '请选择完整日期'
})

const canConfirmDate = computed(() => Boolean(pickerState.value.year && pickerState.value.month && pickerState.value.day))

function parseUserKey(key) {
  const raw = (key || '').trim()
  if (!raw) return { userId: '', username: '' }

  const idMatch = raw.match(/#(\d+)\s*$/)
  if (idMatch?.[1]) return { userId: idMatch[1], username: '' }

  if (/^\d+$/.test(raw)) return { userId: raw, username: '' }

  return { userId: '', username: raw }
}

function getInitialPickerParts(field) {
  const existing = splitDateParts(filters.value[field])
  if (existing) return existing
  const now = new Date()
  return {
    year: String(now.getFullYear()),
    month: pad2(now.getMonth() + 1),
    day: pad2(now.getDate()),
  }
}

function openDatePicker(field) {
  const initial = getInitialPickerParts(field)
  pickerState.value = {
    field,
    year: initial.year,
    month: initial.month,
    day: initial.day,
  }
}

function closeDatePicker() {
  pickerState.value = {
    field: '',
    year: '',
    month: '',
    day: '',
  }
}

function toggleDatePicker(field) {
  if (pickerState.value.field === field) {
    closeDatePicker()
    return
  }
  openDatePicker(field)
}

function clearDateField() {
  if (pickerState.value.field) {
    filters.value[pickerState.value.field] = ''
  }
  closeDatePicker()
}

function selectPickerYear(year) {
  pickerState.value.year = String(year)
  const maxDay = new Date(Number(pickerState.value.year), Number(pickerState.value.month || '01'), 0).getDate()
  if (pickerState.value.day && Number(pickerState.value.day) > maxDay) {
    pickerState.value.day = pad2(maxDay)
  }
}

function selectPickerMonth(month) {
  pickerState.value.month = String(month)
  const maxDay = new Date(Number(pickerState.value.year || new Date().getFullYear()), Number(pickerState.value.month), 0).getDate()
  if (pickerState.value.day && Number(pickerState.value.day) > maxDay) {
    pickerState.value.day = pad2(maxDay)
  }
}

function selectPickerDay(day) {
  pickerState.value.day = String(day)
}

function applyDatePicker() {
  if (!canConfirmDate.value || !pickerState.value.field) return
  filters.value[pickerState.value.field] = `${pickerState.value.year}-${pickerState.value.month}-${pickerState.value.day}`
  closeDatePicker()
}

const rows = computed(() => {
  return (records.value || []).map((r) => {
    const approved = Number(r.approved ?? 0)
    const is_urge = Number(r.is_urge ?? 0)
    const userLabel = (r.username || `用户${r.user_id}`).trim()
    return {
      ...r,
      item_type: r.item_type || 'punch',
      approved,
      is_urge,
      userLabel,
      date: _dateKeyFromTime(r.punch_time),
      time: _timeText(r.punch_time),
      content: r.content || (r.item_type === 'phone' ? '手机号变更申请' : '打卡记录')
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

function toggleCardSelection(id, checked) {
  const next = new Set(selectedIds.value)
  if (checked) next.add(id)
  else next.delete(id)
  selectedIds.value = next
}

function statusKey(row) {
  const approved = Number(row?.approved ?? 0)
  if (approved === 1) return 'approved'
  if (approved === -1) return 'rejected'
  return 'pending'
}

function statusText(row) {
  const approved = Number(row?.approved ?? 0)
  if (approved === 1) return '已审批'
  if (approved === -1) return '已驳回'
  return '待审批'
}

async function load({ append = false } = {}) {
  loading.value = true
  message.value = ''
  try {
    const { userId, username } = parseUserKey(filters.value.search)
    const startDate = (filters.value.startDate || '').trim()
    const endDate = (filters.value.endDate || '').trim()
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
  () => filters.value.search,
  () => {
    scheduleLoad()
  }
)

watch(
  () => [filters.value.startDate, filters.value.endDate],
  () => {
    scheduleLoad()
  },
  { deep: false }
)

async function approveSelected() {
  if (selectedIds.value.size === 0) return
  if (!confirm(`确定通过 ${selectedIds.value.size} 条审批记录吗？`)) return

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
  if (!confirm(`确定驳回 ${selectedIds.value.size} 条审批记录吗？`)) return

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
  max-width: 100%;
  min-height: 100vh;
  overflow-x: clip;
  overscroll-behavior-x: none;
  box-sizing: border-box;
}

.shell {
  width: 100%;
  max-width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow-x: clip;
  box-sizing: border-box;
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
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  overflow-x: clip;
}

.toolbar__title {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
}

.toolbar__titleActions {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.toolbar__grid {
  margin-top: 12px;
  display: grid;
  grid-template-columns: 1.2fr 1fr 1.4fr;
  gap: 10px;
  width: 100%;
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}

.field {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.field--range {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.dateInputs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  width: 100%;
  min-width: 0;
  max-width: 100%;
}

.datePickerGroup {
  position: relative;
  width: 100%;
  min-width: 0;
  max-width: 100%;
}

.dateBox {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  width: 100%;
  min-height: 50px;
  box-sizing: border-box;
  border: 1px solid rgba(15, 23, 42, 0.12);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.94);
  padding: 10px 14px;
  color: rgba(15, 23, 42, 0.86);
  font-size: 14px;
  outline: none;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 4px;
  text-align: left;
  cursor: pointer;
}

.dateBox--active {
  border-color: rgba(24, 59, 77, 0.28);
  box-shadow: 0 0 0 4px rgba(24, 59, 77, 0.08);
}

.dateBox__label {
  font-size: 11px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.45);
}

.dateBox__value {
  display: block;
  width: 100%;
  min-width: 0;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.86);
  font-size: 12px;
  line-height: 1.2;
  white-space: nowrap;
  overflow: visible;
  text-overflow: clip;
}

.pickerOverlay {
  position: fixed;
  inset: 0;
  z-index: 80;
  background: rgba(15, 23, 42, 0.24);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 16px;
  box-sizing: border-box;
}

.pickerSheet {
  width: min(760px, 100%);
  max-width: 100%;
  border-radius: 28px 28px 0 0;
  background: rgba(255, 252, 247, 0.98);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.22);
  padding: 18px;
  display: grid;
  gap: 14px;
  box-sizing: border-box;
  max-height: min(78vh, 720px);
}

.pickerSheet__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.pickerSheet__eyebrow {
  margin: 0;
  font-size: 11px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.45);
}

.pickerSheet__title {
  margin: 4px 0 0;
  font-size: 18px;
  font-weight: 1000;
  color: rgba(15, 23, 42, 0.92);
}

.pickerSheet__summary {
  margin: 0;
  font-size: 13px;
  font-weight: 800;
  color: rgba(15, 23, 42, 0.62);
}

.pickerColumns {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  min-height: 0;
}

.pickerColumn {
  min-width: 0;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 10px;
}

.pickerColumn__head {
  font-size: 12px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.46);
}

.pickerList {
  min-height: 0;
  max-height: 42vh;
  overflow-y: auto;
  overflow-x: hidden;
  display: grid;
  gap: 8px;
  padding-right: 4px;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: rgba(181, 140, 32, 0.4) transparent;
}

.pickerList::-webkit-scrollbar {
  width: 6px;
}

.pickerList::-webkit-scrollbar-thumb {
  background: rgba(181, 140, 32, 0.4);
  border-radius: 999px;
}

.pickerItem {
  min-height: 42px;
  border-radius: 14px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(247, 243, 234, 0.88);
  color: rgba(15, 23, 42, 0.82);
  font-size: 14px;
  font-weight: 900;
  text-align: left;
  padding: 0 14px;
  cursor: pointer;
}

.pickerItem--selected {
  border-color: rgba(181, 140, 32, 0.28);
  background: rgba(196, 155, 40, 0.14);
  color: #7c5b16;
}

.pickerSheet__actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.pickerGhostButton,
.pickerPrimaryButton {
  min-height: 40px;
  border-radius: 999px;
  padding: 0 16px;
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
}

.pickerGhostButton {
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(15, 23, 42, 0.04);
  color: rgba(15, 23, 42, 0.78);
}

.pickerPrimaryButton {
  border: 0;
  background: linear-gradient(135deg, #d4a63a, #b57a23);
  color: #fffdf8;
}

.pickerPrimaryButton:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  min-width: 0;
  max-width: 100%;
}

.left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  min-width: 0;
  max-width: 100%;
}

.label {
  font-size: 12px;
  color: rgba(15, 23, 42, 0.62);
  font-weight: 900;
}

.tableWrap {
  width: 100%;
  max-width: 100%;
  flex: 1;
  overflow-x: clip;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.78);
  border-top: 1px solid rgba(15, 23, 42, 0.08);
  min-height: 0;
  min-width: 0;
  box-sizing: border-box;
}

.mobileList {
  display: none;
  min-width: 0;
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
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
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
  min-width: 0;
  max-width: 100%;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}

.toolbar :deep(.el-input),
.toolbar :deep(.el-input__wrapper),
.toolbar :deep(.el-button),
.more :deep(.el-button) {
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.toolbar :deep(.el-input__inner) {
  min-width: 0;
}

.selectionDock {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 90;
  padding: 12px 16px calc(12px + env(safe-area-inset-bottom, 0px));
  pointer-events: none;
  box-sizing: border-box;
}

.selectionDock__shell {
  width: min(760px, 100%);
  margin: 0 auto;
  border-radius: 24px 24px 0 0;
  background: rgba(255, 252, 247, 0.98);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 -14px 40px rgba(15, 23, 42, 0.14);
  padding: 14px 16px;
  display: grid;
  gap: 12px;
  pointer-events: auto;
  box-sizing: border-box;
}

.selectionDock__main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
}

.selectionDock__check {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  font-size: 13px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.86);
}

.selectionDock__count {
  margin: 0;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.58);
}

.selectionDock__actions {
  display: flex;
  gap: 10px;
}

.selectionDock__actions :deep(.el-button) {
  flex: 1 1 0;
  min-height: 42px;
  border-radius: 999px;
}

.selectionDock-enter-active,
.selectionDock-leave-active {
  transition: opacity 0.24s ease, transform 0.24s ease;
}

.selectionDock-enter-from,
.selectionDock-leave-to {
  opacity: 0;
  transform: translateY(100%);
}

@media (max-width: 900px) {
  .page {
    padding-bottom: 136px;
  }

  .shell {
    background: linear-gradient(180deg, rgba(244, 240, 232, 0.82), rgba(244, 240, 232, 0));
  }

  .toolbar__grid {
    grid-template-columns: 1fr;
  }

  .field--range {
    grid-template-columns: 1fr;
  }

  .toolbar {
    position: relative;
    top: auto;
    background: transparent;
    border-bottom: 0;
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
    padding: 10px 12px 4px;
  }

  .toolbar__title,
  .left,
  .right {
    align-items: stretch;
    width: 100%;
  }

  .toolbar__title {
    flex-direction: column;
  }

  .toolbar__title {
    align-items: flex-start;
    gap: 8px;
  }

  .toolbar__titleActions {
    width: 100%;
  }

  .toolbar__titleActions :deep(.el-button) {
    flex: 1 1 0;
    min-height: 36px;
    padding: 0 14px;
    border-radius: 999px;
  }

  .toolbar__title :deep(.el-button) {
    min-height: 36px;
    padding: 0 14px;
    border-radius: 999px;
  }

  .toolbar__grid {
    margin-top: 10px;
    padding: 12px;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.72);
    border: 1px solid rgba(15, 23, 42, 0.06);
  }

  .left,
  .right {
    gap: 8px;
  }

  .title {
    font-size: 16px;
  }

  .field :deep(.el-input__wrapper),
  .field :deep(.el-textarea__inner) {
    min-height: 44px;
    border-radius: 14px;
  }

  .field :deep(.el-input__inner) {
    font-size: 16px;
  }

  .dateBox {
    min-height: 52px;
    font-size: 16px;
  }

  .dateBox__value {
    font-size: 11px;
  }

  .pickerOverlay {
    padding: 10px;
  }

  .pickerSheet {
    border-radius: 26px 26px 0 0;
    padding: 16px 14px calc(16px + env(safe-area-inset-bottom, 0px));
    max-height: 76vh;
  }

  .pickerColumns {
    gap: 8px;
  }

  .pickerList {
    max-height: 34vh;
  }

  .pickerItem {
    min-height: 40px;
    font-size: 13px;
    padding: 0 10px;
  }

  .pickerSheet__actions {
    justify-content: stretch;
  }

  .pickerGhostButton,
  .pickerPrimaryButton {
    flex: 1 1 0;
  }

  .kicker,
  .label,
  .muted,
  .chk {
    font-size: 11px;
  }

  .right :deep(.el-button),
  .left :deep(.el-button) {
    width: 100%;
  }

  .desktopTable {
    display: none;
  }

  .tableWrap {
    overflow-x: clip;
    overflow-y: visible;
    background: transparent;
    border-top: 0;
    padding: 6px 12px 0;
  }

  .mobileList {
    display: grid;
    gap: 12px;
    width: 100%;
    min-width: 0;
    max-width: 100%;
  }

  .mobileCard {
    border-radius: 22px;
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid rgba(15, 23, 42, 0.08);
    box-shadow: 0 18px 42px rgba(15, 23, 42, 0.1);
    padding: 15px;
    display: grid;
    gap: 12px;
    width: 100%;
    min-width: 0;
    max-width: 100%;
    box-sizing: border-box;
    overflow: hidden;
  }

  .mobileCard__top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
    min-width: 0;
  }

  .mobileCheck {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    font-weight: 900;
    color: rgba(15, 23, 42, 0.82);
  }

  .mobileCheck--ghost {
    color: rgba(15, 23, 42, 0.5);
  }

  .mobileTags {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 8px;
    min-width: 0;
  }

  .pill {
    display: inline-flex;
    align-items: center;
    min-height: 28px;
    padding: 0 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 900;
    border: 1px solid transparent;
  }

  .pill--punch {
    background: rgba(59, 130, 246, 0.12);
    color: #1d4ed8;
  }

  .pill--phone {
    background: rgba(20, 184, 166, 0.12);
    color: #0f766e;
  }

  .pill--pending {
    background: rgba(245, 158, 11, 0.12);
    color: #b45309;
  }

  .pill--approved {
    background: rgba(34, 197, 94, 0.12);
    color: #166534;
  }

  .pill--rejected {
    background: rgba(239, 68, 68, 0.12);
    color: #991b1b;
  }

  .pill--urge {
    background: rgba(244, 63, 94, 0.12);
    color: #be123c;
  }

  .mobileCard__main {
    display: grid;
    gap: 6px;
    min-width: 0;
  }

  .mobileUser {
    margin: 0;
    font-size: 18px;
    font-weight: 1000;
    color: rgba(15, 23, 42, 0.92);
  }

  .mobileContent {
    margin: 0;
    font-size: 13px;
    line-height: 1.6;
    color: rgba(15, 23, 42, 0.66);
    word-break: break-word;
  }

  .mobileMeta {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    margin: 0;
    min-width: 0;
  }

  .mobileMeta__item {
    min-width: 0;
    padding: 10px 12px;
    border-radius: 16px;
    background: rgba(15, 23, 42, 0.04);
  }

  .mobileMeta__item dt {
    margin: 0 0 6px;
    font-size: 11px;
    font-weight: 900;
    color: rgba(15, 23, 42, 0.46);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .mobileMeta__item dd {
    margin: 0;
    font-size: 13px;
    font-weight: 800;
    color: rgba(15, 23, 42, 0.82);
    word-break: break-word;
  }

  .more {
    position: sticky;
    bottom: 0;
    padding: 10px 12px calc(10px + env(safe-area-inset-bottom, 0px));
    background: rgba(255, 255, 255, 0.94);
    overflow-x: clip;
  }

  .more :deep(.el-button) {
    width: 100%;
  }

  .selectionDock {
    padding: 10px 10px calc(10px + env(safe-area-inset-bottom, 0px));
  }

  .selectionDock__shell {
    border-radius: 22px 22px 0 0;
    padding: 12px;
    gap: 10px;
  }

  .selectionDock__main,
  .selectionDock__actions {
    grid-template-columns: 1fr;
  }

  .selectionDock__main {
    display: grid;
    gap: 8px;
  }

  .selectionDock__count {
    font-size: 11px;
  }

  .selectionDock__actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
}
</style>
