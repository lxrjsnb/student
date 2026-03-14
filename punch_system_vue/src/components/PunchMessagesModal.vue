<template>
  <div v-if="open" class="wrap" role="dialog" aria-modal="true" @click.self="$emit('close')">
    <div class="panel">
      <div class="head">
        <h3 class="title">打卡消息</h3>
        <button class="x" type="button" @click="$emit('close')" aria-label="关闭">✕</button>
      </div>

      <div class="body">
        <div v-if="loading" class="empty">加载中…</div>
        <template v-else>
          <div v-if="message" class="tip" :class="`tip--${messageType}`">{{ message }}</div>

          <ul v-if="normalized.length" class="list" aria-label="打卡审批消息列表">
            <li v-for="row in normalized" :key="row.id" class="item">
              <div class="meta">
                <div class="time">
                  <span class="id">#{{ row.id }}</span>
                  <span class="sep">·</span>
                  <span>{{ row.time }}</span>
                </div>
                <span class="status" :class="`status--${row.statusKey}`">{{ row.statusText }}</span>
              </div>

              <div class="actions">
                <button
                  v-if="row.statusKey === 'pending'"
                  class="urge"
                  type="button"
                  :disabled="row.isUrged"
                  @click="$emit('urge', row.id)"
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
  return normalized || raw
}

const normalized = computed(() => {
  return (props.records || []).map((r) => {
    const approved = Number(r?.approved ?? 0)
    const isUrged = Number(r?.is_urge ?? 0) === 1
    const statusKey = approved === 1 ? 'approved' : approved === -1 ? 'rejected' : 'pending'
    const statusText = approved === 1 ? '通过' : approved === -1 ? '驳回' : '待审批'
    return {
      id: r?.id,
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
  background: rgba(15, 23, 42, 0.4);
  display: grid;
  place-items: center;
  z-index: 50;
  padding: 18px;
}

.panel {
  width: min(520px, 92vw);
  max-height: min(640px, 86vh);
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(12px);
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 28px 70px rgba(15, 23, 42, 0.28);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.head {
  padding: 14px 14px 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
}

.title {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.9);
}

.x {
  border: 0;
  width: 34px;
  height: 34px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.06);
  color: rgba(15, 23, 42, 0.85);
  cursor: pointer;
}

.body {
  padding: 12px 14px 14px;
  overflow: auto;
}

.empty {
  padding: 20px 0;
  text-align: center;
  color: rgba(15, 23, 42, 0.55);
  font-weight: 700;
  font-size: 13px;
}

.tip {
  border-radius: 14px;
  padding: 10px 12px;
  border: 1px solid transparent;
  font-size: 13px;
  font-weight: 800;
}

.tip--error {
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
  border-color: rgba(239, 68, 68, 0.25);
}

.tip--info {
  background: rgba(0, 168, 204, 0.12);
  color: #008ba8;
  border-color: rgba(0, 168, 204, 0.25);
}

.list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 10px;
}

.item {
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.72);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.meta {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.time {
  color: rgba(15, 23, 42, 0.78);
  font-weight: 800;
  font-size: 13px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.id {
  color: rgba(15, 23, 42, 0.55);
  font-weight: 900;
}

.sep {
  opacity: 0.45;
}

.status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  padding: 4px 10px;
  border-radius: 999px;
  font-weight: 900;
  font-size: 12px;
  border: 1px solid transparent;
}

.status--pending {
  background: rgba(234, 179, 8, 0.12);
  color: rgba(133, 77, 14, 0.95);
  border-color: rgba(234, 179, 8, 0.22);
}

.status--approved {
  background: rgba(34, 197, 94, 0.12);
  color: #15803d;
  border-color: rgba(34, 197, 94, 0.22);
}

.status--rejected {
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
  border-color: rgba(239, 68, 68, 0.22);
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.urge {
  border: 1px solid rgba(0, 168, 204, 0.3);
  background: rgba(0, 168, 204, 0.12);
  color: rgba(0, 95, 120, 0.95);
  font-weight: 900;
  font-size: 12px;
  padding: 7px 10px;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.12s ease, filter 0.12s ease, opacity 0.12s ease;
}

.urge:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.urge:hover:not(:disabled) {
  transform: translateY(-1px);
  filter: drop-shadow(0 12px 18px rgba(0, 168, 204, 0.22));
}
</style>
