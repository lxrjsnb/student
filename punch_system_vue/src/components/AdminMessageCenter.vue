<template>
  <teleport to="body">
    <div v-if="open" class="overlay" @click="$emit('close')">
      <section class="sheet" @click.stop>
        <div class="head">
          <div>
            <p class="eyebrow">Messages</p>
            <h3 class="title">消息</h3>
          </div>
          <button class="closeBtn" type="button" @click="$emit('close')">关闭</button>
        </div>

        <div v-if="message" class="notice" :class="`notice--${messageType}`">{{ message }}</div>

        <div v-if="loading" class="empty">加载中…</div>
        <div v-else-if="items.length" class="list">
          <article v-for="item in items" :key="item.id" class="card">
            <button class="cardMain" type="button" :disabled="!item.can_open" @click="$emit('open-item', item)">
              <div class="cardTop">
                <span class="kind">{{ kindText(item.item_type) }}</span>
                <span class="status" :class="`status--${item.status || 'pending'}`">{{ statusText(item.status) }}</span>
              </div>
              <h4 class="cardTitle">{{ item.title }}</h4>
              <p class="cardSub">{{ item.subtitle }}</p>
              <p class="cardDetail">{{ item.detail }}</p>
              <p class="cardTime">{{ formatDateTime(item.updated_at || item.created_at) }}</p>
            </button>

            <div v-if="item.can_urge" class="cardActions">
              <button class="urgeBtn" type="button" :disabled="item.is_urge === 1" @click="$emit('urge-item', item)">
                {{ item.is_urge === 1 ? '已催办' : '催办' }}
              </button>
            </div>
          </article>
        </div>
        <div v-else class="empty">暂无消息</div>
      </section>
    </div>
  </teleport>
</template>

<script setup>
defineProps({
  open: { type: Boolean, default: false },
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  message: { type: String, default: '' },
  messageType: { type: String, default: 'info' }
})

defineEmits(['close', 'open-item', 'urge-item'])

function statusText(status) {
  if (status === 'approved') return '已通过'
  if (status === 'active') return '生效中'
  if (status === 'scheduled') return '待生效'
  if (status === 'rejected' || status === 'revoked') return status === 'revoked' ? '已收回' : '已驳回'
  if (status === 'expired') return '已到期'
  return '待处理'
}

function kindText(type) {
  if (type === 'activity_review' || type === 'activity_submission') return '活动'
  if (type === 'delegation_review' || type === 'delegation_application' || type === 'delegation_grant') return '放权'
  return '消息'
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
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.28);
  display: grid;
  place-items: center;
  padding: 18px;
  z-index: 120;
}

.sheet {
  width: min(720px, 100%);
  max-height: min(82vh, 920px);
  overflow: auto;
  padding: 22px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(24, 33, 47, 0.08);
  box-shadow: 0 30px 80px rgba(20, 29, 41, 0.18);
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(24, 59, 77, 0.54);
}

.title {
  margin: 0;
  font-size: 30px;
  line-height: 1;
  letter-spacing: -0.05em;
  color: #152131;
}

.closeBtn,
.urgeBtn {
  border: 0;
  border-radius: 999px;
  min-height: 38px;
  padding: 0 14px;
  font-size: 13px;
  font-weight: 800;
}

.closeBtn {
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
}

.urgeBtn {
  background: rgba(215, 177, 120, 0.18);
  color: #7a5d23;
}

.notice {
  margin-bottom: 16px;
  padding: 12px 14px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 800;
}

.notice--error {
  background: rgba(239, 68, 68, 0.12);
  color: #991b1b;
}

.notice--success,
.notice--info {
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
}

.list {
  display: grid;
  gap: 12px;
}

.card {
  border-radius: 20px;
  background: rgba(248, 242, 231, 0.62);
  border: 1px solid rgba(24, 33, 47, 0.06);
  overflow: hidden;
}

.cardMain {
  width: 100%;
  border: 0;
  background: transparent;
  padding: 16px;
  text-align: left;
}

.cardTop {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.kind,
.status {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
}

.kind {
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
}

.status--approved {
  background: rgba(34, 197, 94, 0.14);
  color: #166534;
}

.status--active {
  background: rgba(34, 197, 94, 0.14);
  color: #166534;
}

.status--rejected,
.status--revoked {
  background: rgba(239, 68, 68, 0.14);
  color: #991b1b;
}

.status--expired {
  background: rgba(148, 163, 184, 0.18);
  color: #475569;
}

.status--scheduled {
  background: rgba(59, 130, 246, 0.12);
  color: #1d4ed8;
}

.status--pending {
  background: rgba(245, 158, 11, 0.14);
  color: #b45309;
}

.cardTitle {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: #152131;
}

.cardSub,
.cardDetail,
.cardTime,
.empty {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: rgba(24, 33, 47, 0.62);
}

.cardActions {
  padding: 0 16px 16px;
}

.empty {
  text-align: center;
  padding: 24px 8px;
}

@media (max-width: 768px) {
  .overlay {
    padding: 0;
    align-items: end;
  }

  .sheet {
    width: 100%;
    max-height: 86vh;
    border-radius: 24px 24px 0 0;
    padding: 18px 16px calc(18px + env(safe-area-inset-bottom, 0px));
  }
}
</style>
