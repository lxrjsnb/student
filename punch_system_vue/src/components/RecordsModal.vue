<template>
  <div v-if="open" class="wrap" role="dialog" aria-modal="true" @click.self="$emit('close')">
    <div class="panel">
      <div class="head">
        <div class="monthSwitch">
          <button class="navBtn" type="button" :disabled="loading" @click="prevMonth" aria-label="上个月">‹</button>
          <h3 class="title">{{ monthLabel }}</h3>
          <button class="navBtn" type="button" :disabled="loading" @click="nextMonth" aria-label="下个月">›</button>
        </div>
        <div class="headRight">
          <button class="x" type="button" @click="$emit('close')" aria-label="关闭">✕</button>
        </div>
      </div>

      <div class="body">
        <div v-if="loading" class="empty">加载中…</div>
        <template v-else>
          <div class="stats" aria-label="月度统计">
            <div v-for="item in monthStats" :key="item.label" class="stat">
              <div class="statValue">{{ item.value }}</div>
              <div class="statLabel">{{ item.label }}</div>
            </div>
          </div>

          <div class="week">
            <span v-for="w in weekDays" :key="w" class="weekCell">{{ w }}</span>
          </div>

          <div class="grid" role="grid" aria-label="打卡日历">
            <button
              v-for="cell in calendarCells"
              :key="cell.key"
              class="day"
              :class="{
                'day--muted': !cell.inMonth,
                'day--today': cell.isToday,
                'day--has': cell.hasAny,
                'day--selected': selected?.key === cell.key
              }"
              type="button"
              @click="openDay(cell)"
            >
              <span class="num">{{ cell.day }}</span>
              <span v-if="cell.marks.length" class="marks" aria-label="当日记录状态">
                <span
                  v-for="mark in cell.marks"
                  :key="mark"
                  class="mark"
                  :class="`mark--${mark}`"
                ></span>
              </span>
            </button>
          </div>

          <div v-if="selected" class="detail">
            <div class="detailHead">
              <p class="detailTitle">{{ selected.label }}</p>
              <button class="detailClose" type="button" @click="selected = null" aria-label="关闭详情">✕</button>
            </div>
            <ul class="detailList">
              <li v-for="(row, idx) in selected.times" :key="idx" class="detailRow">
                <span class="detailDot" :class="`detailDot--${row.statusKey}`" aria-hidden="true"></span>
                <span class="detailTime">{{ row.time }}</span>
                <span class="detailStatus" :class="`detailStatus--${row.statusKey}`">{{ row.statusText }}</span>
              </li>
            </ul>
          </div>

          <div v-else-if="!records?.length" class="empty">本月还没有打卡记录</div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  records: { type: Array, default: () => [] }
})

defineEmits(['close'])

const weekDays = ['日', '一', '二', '三', '四', '五', '六']
const viewDate = ref(new Date())
const selected = ref(null)

watch(
  () => props.open,
  (isOpen) => {
    if (!isOpen) {
      selected.value = null
      return
    }
    viewDate.value = new Date()
    selected.value = null
  }
)

const monthLabel = computed(() => {
  const y = viewDate.value.getFullYear()
  const m = viewDate.value.getMonth() + 1
  return `${y} 年 ${String(m).padStart(2, '0')} 月`
})

const monthRecordKeys = computed(() => {
  const y = viewDate.value.getFullYear()
  const m = viewDate.value.getMonth()
  const prefix = `${y}-${String(m + 1).padStart(2, '0')}-`
  return [...recordsByDay.value.keys()].filter((key) => key.startsWith(prefix))
})

const monthStats = computed(() => {
  const monthKeys = monthRecordKeys.value
  const monthRows = monthKeys.flatMap((key) => recordsByDay.value.get(key) || [])
  const monthRecordCount = monthRows.filter((row) => Number(row?.approved) === 1).length
  const activeDays = monthKeys.length
  const pendingCount = monthRows.filter((row) => Number(row?.approved) === 0).length
  const rejectedCount = monthRows.filter((row) => Number(row?.approved) === -1).length
  return [
    { label: '本月记录', value: monthRecordCount },
    { label: '打卡天数', value: activeDays },
    { label: '待审批', value: pendingCount },
    { label: '被驳回', value: rejectedCount }
  ]
})

const recordsByDay = computed(() => {
  const map = new Map()
  for (const r of props.records || []) {
    const raw = r?.punch_time_raw || r?.punch_time || ''
    const strictKey = extractDateKey(raw) || extractRfcDateKey(raw)
    const date = strictKey ? null : parseDbDate(raw)
    const key = strictKey || (date ? toKey(date) : '')
    if (!key) continue

    const time = date
      ? date.toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
      : (extractTime(raw) || extractTime(String(r?.punch_time || '')) || '-')

    const arr = map.get(key) || []
    arr.push({
      raw: String(raw || ''),
      time,
      ts: date ? date.getTime() : Number.NaN,
      approved: Number(r?.approved ?? 1)
    })
    map.set(key, arr)
  }
  for (const arr of map.values()) {
    arr.sort((a, b) => {
      const at = Number.isFinite(a.ts) ? a.ts : Number.POSITIVE_INFINITY
      const bt = Number.isFinite(b.ts) ? b.ts : Number.POSITIVE_INFINITY
      if (at !== bt) return at - bt
      return (a.raw || '').localeCompare(b.raw || '')
    })
  }
  return map
})

const calendarCells = computed(() => {
  const y = viewDate.value.getFullYear()
  const m = viewDate.value.getMonth()
  const first = new Date(y, m, 1)
  const startIndex = first.getDay()
  const start = new Date(y, m, 1 - startIndex)
  const todayKey = toKey(new Date())

  const cells = []
  for (let i = 0; i < 42; i++) {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    const key = toKey(d)
    const inMonth = d.getMonth() === m
    const rows = recordsByDay.value.get(key) || []
    const marks = []
    if (inMonth) {
      if (rows.some((row) => Number(row?.approved) === -1)) marks.push('rejected')
      if (rows.some((row) => Number(row?.approved) === 0)) marks.push('pending')
      if (rows.some((row) => Number(row?.approved) === 1)) marks.push('approved')
    }
    cells.push({
      key,
      inMonth,
      isToday: key === todayKey,
      day: d.getDate(),
      count: inMonth ? rows.length : 0,
      hasAny: inMonth ? rows.length > 0 : false,
      marks
    })
  }
  return cells
})

function prevMonth() {
  const d = new Date(viewDate.value)
  d.setMonth(d.getMonth() - 1)
  viewDate.value = d
  selected.value = null
}

function nextMonth() {
  const d = new Date(viewDate.value)
  d.setMonth(d.getMonth() + 1)
  viewDate.value = d
  selected.value = null
}

function openDay(cell) {
  if (!cell?.count) return
  const times = (recordsByDay.value.get(cell.key) || []).map((row) => ({
    time: row.time,
    statusKey: getStatusKey(row.approved),
    statusText: getStatusText(row.approved)
  }))
  const pretty = cell.key.replace(/^(\d{4})-(\d{2})-(\d{2})$/, '$1年$2月$3日')
  selected.value = {
    key: cell.key,
    label: `${pretty} · 当日记录`,
    times
  }
}

function getStatusKey(approved) {
  const value = Number(approved ?? 0)
  if (value === -1) return 'rejected'
  if (value === 0) return 'pending'
  return 'approved'
}

function getStatusText(approved) {
  const key = getStatusKey(approved)
  if (key === 'rejected') return '已驳回'
  if (key === 'pending') return '待审批'
  return '已通过'
}

function toKey(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function extractDateKey(text) {
  const m = String(text).match(/(\d{4})[/-](\d{1,2})[/-](\d{1,2})/)
  if (!m) return ''
  const y = m[1]
  const mo = String(Number(m[2])).padStart(2, '0')
  const d = String(Number(m[3])).padStart(2, '0')
  return `${y}-${mo}-${d}`
}

function extractRfcDateKey(text) {
  // e.g. "Sat, 14 Mar 2026 08:00:00 GMT"
  const m = String(text).match(/\b(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})\b/)
  if (!m) return ''
  const day = String(Number(m[1])).padStart(2, '0')
  const month = monthFromShortName(m[2])
  if (!month) return ''
  const year = m[3]
  return `${year}-${month}-${day}`
}

function monthFromShortName(mon) {
  const k = String(mon || '').toLowerCase()
  const map = {
    jan: '01',
    feb: '02',
    mar: '03',
    apr: '04',
    may: '05',
    jun: '06',
    jul: '07',
    aug: '08',
    sep: '09',
    oct: '10',
    nov: '11',
    dec: '12'
  }
  return map[k] || ''
}

function extractTime(text) {
  const m = String(text).match(/(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?/)
  if (!m) return ''
  const hh = String(Number(m[1])).padStart(2, '0')
  const mm = String(Number(m[2])).padStart(2, '0')
  const ss = String(Number(m[3] || '0')).padStart(2, '0')
  return `${hh}:${mm}:${ss}`
}

function parseDbDate(text) {
  if (!text) return null
  const str = String(text).trim()

  if (/^\d{13}$/.test(str)) {
    const d = new Date(Number(str))
    return Number.isNaN(d.getTime()) ? null : d
  }

  // ISO / RFC
  if (/^\d{4}-\d{2}-\d{2}T/.test(str) || /Z$/.test(str) || /[+-]\d{2}:?\d{2}$/.test(str)) {
    const d = new Date(str)
    return Number.isNaN(d.getTime()) ? null : d
  }

  // "YYYY-MM-DD HH:mm:ss" or "YYYY/MM/DD HH:mm:ss" -> treat as local time
  const m = str.match(/(\d{4})[/-](\d{1,2})[/-](\d{1,2})(?:\s+(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?/)
  if (!m) return null
  const year = Number(m[1])
  const month = Number(m[2]) - 1
  const day = Number(m[3])
  const hh = Number(m[4] || 0)
  const mm = Number(m[5] || 0)
  const ss = Number(m[6] || 0)
  const d = new Date(year, month, day, hh, mm, ss)
  return Number.isNaN(d.getTime()) ? null : d
}
</script>

<style scoped>
.wrap {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.22);
  display: grid;
  place-items: center;
  padding: 18px;
  z-index: 40;
}

.panel {
  width: min(520px, 100%);
  border-radius: 0;
  background: #f7f4ee;
  border: 1px solid rgba(24, 33, 47, 0.04);
  box-shadow: 0 18px 54px rgba(52, 71, 97, 0.14);
  overflow: hidden;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 16px 12px;
  border-bottom: 1px solid rgba(24, 33, 47, 0.06);
}

.monthSwitch {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.title {
  margin: 0;
  min-width: 124px;
  text-align: center;
  font-size: 18px;
  font-weight: 800;
  color: #2b3542;
  letter-spacing: 0.01em;
}

.headRight {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.navBtn {
  border: 0;
  background: transparent;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  color: rgba(43, 53, 66, 0.78);
  font-weight: 900;
  font-size: 20px;
}

.navBtn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.x {
  border: 0;
  background: transparent;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  color: rgba(43, 53, 66, 0.72);
}

.body {
  padding: 10px 14px 18px;
  max-height: min(76vh, 680px);
  overflow: auto;
}

.empty {
  padding: 28px 0;
  text-align: center;
  color: rgba(15, 23, 42, 0.6);
  font-size: 13px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.stat {
  padding: 10px 6px 8px;
  text-align: center;
}

.statValue {
  font-size: 23px;
  line-height: 1;
  font-weight: 800;
  color: #d75f36;
}

.statLabel {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(43, 53, 66, 0.68);
  font-weight: 600;
}

.week {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
  margin-bottom: 4px;
}

.weekCell {
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  color: rgba(43, 53, 66, 0.66);
  padding: 6px 0;
}

.grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px 2px;
}

.day {
  position: relative;
  min-height: 58px;
  border-radius: 18px;
  border: 0;
  background: transparent;
  color: rgba(43, 53, 66, 0.88);
  display: grid;
  align-content: start;
  justify-items: center;
  padding: 8px 0 6px;
  transition: background 0.15s ease, color 0.15s ease, transform 0.15s ease;
}

.day:hover {
  background: rgba(24, 59, 77, 0.04);
}

.day--muted {
  color: rgba(43, 53, 66, 0.32);
}

.day--today {
  background: rgba(96, 196, 183, 0.16);
}

.day--has {
  color: #2b3542;
}

.day--selected,
.day--today.day--selected {
  background: rgba(96, 196, 183, 0.22);
}

.num {
  font-size: 22px;
  font-weight: 800;
}

.marks {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
}

.mark {
  width: 5px;
  height: 5px;
  border-radius: 999px;
}

.mark--rejected {
  background: #ee4f3a;
}

.mark--pending {
  background: #d8a53a;
}

.mark--approved {
  background: #60c4b7;
}

.detail {
  margin-top: 16px;
  border-top: 1px solid rgba(24, 33, 47, 0.08);
  padding-top: 14px;
}

.detailHead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.detailTitle {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  color: rgba(43, 53, 66, 0.88);
}

.detailClose {
  border: 0;
  width: 30px;
  height: 30px;
  border-radius: 999px;
  background: rgba(24, 59, 77, 0.06);
  color: rgba(43, 53, 66, 0.68);
}

.detailList {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.detailRow {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 4px;
  border-bottom: 1px dashed rgba(24, 33, 47, 0.08);
}

.detailDot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #60c4b7;
}

.detailTime {
  font-size: 14px;
  color: rgba(43, 53, 66, 0.82);
}

.detailStatus {
  margin-left: auto;
  font-size: 12px;
  font-weight: 700;
}

.detailDot--rejected,
.detailStatus--rejected {
  color: #ee4f3a;
  background-color: #ee4f3a;
}

.detailDot--pending,
.detailStatus--pending {
  color: #d8a53a;
  background-color: #d8a53a;
}

.detailDot--approved,
.detailStatus--approved {
  color: #60c4b7;
  background-color: #60c4b7;
}

.detailDot--rejected,
.detailDot--pending,
.detailDot--approved {
  box-shadow: none;
}

.detailStatus--rejected,
.detailStatus--pending,
.detailStatus--approved {
  background: transparent;
}

@media (max-width: 640px) {
  .wrap {
    padding: 0;
    align-items: end;
  }

  .panel {
    width: 100%;
    min-height: 78vh;
  }

  .stats {
    gap: 4px;
  }

  .statValue {
    font-size: 20px;
  }

  .day {
    min-height: 54px;
  }

  .num {
    font-size: 20px;
  }
}
</style>
