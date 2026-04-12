<template>
  <div v-if="open" class="wrap" role="dialog" aria-modal="true" @click.self="$emit('close')">
    <div class="panel">
      <div class="head">
        <h3 class="title">消息</h3>
        <button class="x" type="button" @click="$emit('close')" aria-label="关闭">✕</button>
      </div>

      <div class="body">
        <div v-if="loading" class="empty">加载中…</div>
        <template v-else>
          <div v-if="message" class="tip" :class="`tip--${messageType}`">{{ message }}</div>

          <ul v-if="normalized.length" class="list" aria-label="消息列表">
            <li v-for="row in normalized" :key="row.id" class="item">
              <div class="meta">
                <div class="kind">{{ row.title }}</div>
                <div class="time">
                  <span>{{ row.time }}</span>
                </div>
                <div v-if="row.detail" class="detail">{{ row.detail }}</div>
                <span class="status" :class="`status--${row.statusKey}`">{{ row.statusText }}</span>
              </div>

              <div class="actions">
                <button
                  v-if="row.statusKey === 'pending'"
                  class="urge"
                  type="button"
                  :disabled="row.isUrged"
                  @click="$emit('urge', row)"
                >
                  {{ row.isUrged ? '已催办' : '催办' }}
                </button>
              </div>
            </li>
          </ul>

          <div v-else class="empty">暂无消息</div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  records: { type: Array, default: () => [] },
  message: { type: String, default: '' },
  messageType: { type: String, default: 'info' }
})

defineEmits(['close', 'urge'])

function _fmt(text) {
  const raw = String(text || '').trim()
  if (!raw) return '-'
  const normalized = raw.replace('T', ' ').replace('.000Z', '').replace('Z', '').trim()
  const parsed = new Date(normalized)
  if (!Number.isNaN(parsed.getTime())) {
    return _formatChineseDate(parsed)
  }

  const rfcMatch = normalized.match(/\b(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})\s+(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?/)
  if (rfcMatch) {
    const day = String(Number(rfcMatch[1])).padStart(2, '0')
    const month = _monthFromShortName(rfcMatch[2])
    const year = rfcMatch[3]
    const hour = String(Number(rfcMatch[4])).padStart(2, '0')
    const minute = String(Number(rfcMatch[5])).padStart(2, '0')
    const second = String(Number(rfcMatch[6] || '0')).padStart(2, '0')
    if (month) {
      const parsedRfc = new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}`)
      if (!Number.isNaN(parsedRfc.getTime())) return _formatChineseDate(parsedRfc)
      return `${year}年${month}月${day}日 ${hour}:${minute}:${second}`
    }
  }

  return normalized
}

function _formatChineseDate(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  const second = String(date.getSeconds()).padStart(2, '0')
  const weekDays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  const weekDay = weekDays[date.getDay()] || ''
  return `${year}年${month}月${day}日 ${weekDay} ${hour}:${minute}:${second}`
}

function _monthFromShortName(mon) {
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
  return map[String(mon || '').toLowerCase()] || ''
}

const normalized = computed(() => {
  return (props.records || []).map((r) => {
    const approved = Number(r?.approved ?? 0)
    const isUrged = Number(r?.is_urge ?? 0) === 1
    const statusKey = approved === 1 ? 'approved' : approved === -1 ? 'rejected' : 'pending'
    const statusText = approved === 1 ? '通过' : approved === -1 ? '驳回' : '待审批'
    return {
      id: r?.id,
      item_type: r?.item_type || 'punch',
      title: r?.title || '打卡记录',
      detail: r?.detail || '',
      time: _fmt(r?.punch_time),
      statusKey,
      statusText,
      isUrged
    }
  })
})
</script>

<style scoped>
.wrap {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.22);
  display: grid;
  place-items: center;
  z-index: 50;
  padding: 18px;
}

.panel {
  width: min(520px, 100%);
  max-height: min(76vh, 680px);
  background: #f7f4ee;
  border-radius: 0;
  border: 1px solid rgba(24, 33, 47, 0.04);
  box-shadow: 0 18px 54px rgba(52, 71, 97, 0.14);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.head {
  padding: 14px 16px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(24, 33, 47, 0.06);
}

.title {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: #2b3542;
  letter-spacing: 0.01em;
}

.x {
  border: 0;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  background: transparent;
  color: rgba(43, 53, 66, 0.72);
  cursor: pointer;
}

.body {
  padding: 12px 14px 18px;
  overflow: auto;
}

.empty {
  padding: 28px 0;
  text-align: center;
  color: rgba(43, 53, 66, 0.6);
  font-weight: 700;
  font-size: 13px;
}

.tip {
  margin-bottom: 12px;
  border-radius: 14px;
  padding: 10px 12px;
  border: 1px solid transparent;
  font-size: 13px;
  font-weight: 800;
}

.tip--error {
  background: rgba(238, 79, 58, 0.1);
  color: #c04634;
  border-color: rgba(238, 79, 58, 0.18);
}

.tip--info {
  background: rgba(96, 196, 183, 0.12);
  color: #2f8378;
  border-color: rgba(96, 196, 183, 0.18);
}

.list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0;
}

.item {
  padding: 14px 2px;
  border-bottom: 1px dashed rgba(24, 33, 47, 0.08);
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.meta {
  min-width: 0;
  display: grid;
  gap: 6px;
}

.kind {
  color: rgba(43, 53, 66, 0.56);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.time {
  color: rgba(43, 53, 66, 0.82);
  font-weight: 800;
  font-size: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.detail {
  color: rgba(43, 53, 66, 0.66);
  font-size: 13px;
  line-height: 1.5;
}

.status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  padding: 4px 10px;
  border-radius: 999px;
  font-weight: 800;
  font-size: 12px;
  border: 1px solid transparent;
}

.status--pending {
  background: rgba(216, 165, 58, 0.12);
  color: #9d741b;
  border-color: rgba(216, 165, 58, 0.18);
}

.status--approved {
  background: rgba(96, 196, 183, 0.12);
  color: #2f8378;
  border-color: rgba(96, 196, 183, 0.18);
}

.status--rejected {
  background: rgba(238, 79, 58, 0.1);
  color: #c04634;
  border-color: rgba(238, 79, 58, 0.16);
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.urge {
  border: 1px solid rgba(183, 139, 74, 0.18);
  background: rgba(215, 177, 120, 0.16);
  color: #805c20;
  font-weight: 800;
  font-size: 12px;
  padding: 8px 12px;
  border-radius: 999px;
  cursor: pointer;
  transition: transform 0.12s ease, opacity 0.12s ease, background 0.12s ease;
}

.urge:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.urge:hover:not(:disabled) {
  transform: translateY(-1px);
  background: rgba(215, 177, 120, 0.22);
}

@media (max-width: 640px) {
  .wrap {
    padding: 0;
    align-items: end;
  }

  .panel {
    width: 100%;
    min-height: 68vh;
  }

  .item {
    padding: 14px 0;
  }
}
</style>
