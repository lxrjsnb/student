<template>
  <div v-if="open" class="wrap" role="dialog" aria-modal="true" @click.self="$emit('close')">
    <div class="panel">
      <div class="head">
        <button class="navBtn" type="button" :disabled="loading" @click="prevMonth" aria-label="上个月">‹</button>
        <h3 class="title">{{ monthLabel }}</h3>
        <div class="headRight">
          <button class="navBtn" type="button" :disabled="loading" @click="nextMonth" aria-label="下个月">›</button>
          <button class="x" type="button" @click="$emit('close')" aria-label="关闭">✕</button>
        </div>
      </div>

      <div class="body">
        <div v-if="loading" class="empty">加载中…</div>
        <template v-else>
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
                'day--has': cell.count > 0
              }"
              type="button"
              @click="openDay(cell)"
            >
              <span class="num">{{ cell.day }}</span>
              <span v-if="cell.count > 0" class="badge" aria-label="当日打卡次数">{{ cell.count }}</span>
            </button>
          </div>

          <div v-if="selected" class="detail">
            <div class="detailHead">
              <p class="detailTitle">{{ selected.label }}</p>
              <button class="detailClose" type="button" @click="selected = null" aria-label="关闭详情">✕</button>
            </div>
            <ul class="detailList">
              <li v-for="(t, idx) in selected.times" :key="idx" class="detailRow">
                <span class="detailDot" aria-hidden="true"></span>
                <span class="detailTime">{{ t }}</span>
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

const weekDays = ['一', '二', '三', '四', '五', '六', '日']
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
    arr.push({ raw: String(raw || ''), time, ts: date ? date.getTime() : Number.NaN })
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
  const startIndex = (first.getDay() + 6) % 7 // Monday = 0
  const start = new Date(y, m, 1 - startIndex)
  const todayKey = toKey(new Date())

  const cells = []
  for (let i = 0; i < 42; i++) {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    const key = toKey(d)
    const inMonth = d.getMonth() === m
    const times = recordsByDay.value.get(key) || []
    cells.push({
      key,
      inMonth,
      isToday: key === todayKey,
      day: d.getDate(),
      count: inMonth ? times.length : 0
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
  const times = (recordsByDay.value.get(cell.key) || []).map((t) => t.time)
  const pretty = cell.key.replace(/^(\d{4})-(\d{2})-(\d{2})$/, '$1年$2月$3日')
  selected.value = {
    key: cell.key,
    label: `${pretty} · 打卡详情`,
    times
  }
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
  background: rgba(2, 6, 23, 0.35);
  display: grid;
  place-items: center;
  padding: 18px;
  z-index: 40;
}

.panel {
  width: min(520px, 100%);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 26px 70px rgba(15, 23, 42, 0.28);
  overflow: hidden;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.title {
  margin: 0;
  font-size: 14px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.88);
  letter-spacing: 0.2px;
}

.headRight {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.navBtn {
  border: 0;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(0, 0, 0, 0.06);
  width: 32px;
  height: 32px;
  border-radius: 12px;
  color: rgba(15, 23, 42, 0.7);
  font-weight: 900;
}

.navBtn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.x {
  border: 0;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(0, 0, 0, 0.06);
  width: 32px;
  height: 32px;
  border-radius: 12px;
  color: rgba(15, 23, 42, 0.7);
}

.body {
  padding: 12px 16px 16px;
  max-height: min(64vh, 520px);
  overflow: auto;
}

.empty {
  padding: 28px 0;
  text-align: center;
  color: rgba(15, 23, 42, 0.6);
  font-size: 13px;
}

.week {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
  margin-bottom: 8px;
}

.weekCell {
  text-align: center;
  font-size: 12px;
  font-weight: 800;
  color: rgba(15, 23, 42, 0.55);
}

.grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
}

.day {
  position: relative;
  height: 44px;
  border-radius: 14px;
  border: 1px solid rgba(0, 0, 0, 0.04);
  background: rgba(255, 255, 255, 0.62);
  color: rgba(15, 23, 42, 0.82);
  display: grid;
  place-items: center;
  padding: 0;
  transition: transform 0.15s ease, background 0.15s ease, border-color 0.15s ease;
}

.day:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.78);
}

.day--muted {
  opacity: 0.45;
}

.day--today {
  border-color: rgba(0, 168, 204, 0.45);
  box-shadow: 0 0 0 4px rgba(0, 168, 204, 0.1);
}

.day--has {
  border-color: rgba(0, 168, 204, 0.22);
}

.num {
  font-size: 13px;
  font-weight: 800;
}

.badge {
  position: absolute;
  right: 6px;
  bottom: 6px;
  min-width: 18px;
  height: 18px;
  padding: 0 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(0, 168, 204, 0.92);
  color: white;
  font-size: 11px;
  font-weight: 900;
  box-shadow: 0 10px 18px rgba(0, 168, 204, 0.22);
}

.detail {
  margin-top: 12px;
  border-radius: 18px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.04);
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
  font-size: 13px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.84);
}

.detailClose {
  border: 0;
  width: 30px;
  height: 30px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.06);
  color: rgba(15, 23, 42, 0.65);
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
  padding: 10px 10px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.66);
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.detailDot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: rgba(0, 168, 204, 0.95);
  box-shadow: 0 0 0 6px rgba(0, 168, 204, 0.12);
}

.detailTime {
  font-size: 13px;
  color: rgba(15, 23, 42, 0.78);
}
</style>
