<template>
  <section class="wrap">
    <div class="card">
      <div class="head">
        <div class="avatar" aria-hidden="true"></div>
        <div class="meta">
          <h1 class="title">{{ user.username }}</h1>
          <div class="sub">用户ID：{{ user.id }}</div>
        </div>
        <div class="actions">
          <button class="btn btn--ghost" type="button" @click="$emit('goHome')">返回打卡</button>
          <button class="btn btn--danger" type="button" @click="$emit('logout')">退出登录</button>
        </div>
      </div>

      <div class="grid">
        <div class="stat">
          <div class="stat__k">今日状态</div>
          <div class="stat__v">
            <span v-if="todayRecord" class="tag tag--ok">已打卡</span>
            <span v-else class="tag tag--warn">未打卡</span>
          </div>
        </div>
        <div class="stat">
          <div class="stat__k">今日打卡时间</div>
          <div class="stat__v mono">{{ todayRecord?.punch_time || '—' }}</div>
        </div>
        <div class="stat">
          <div class="stat__k">累计记录</div>
          <div class="stat__v mono">{{ total }}</div>
        </div>
        <div class="stat">
          <div class="stat__k">最近一次</div>
          <div class="stat__v mono">{{ latest?.punch_time || '—' }}</div>
        </div>
      </div>

      <div class="panel">
        <div class="panel__head">
          <div>
            <h2 class="panel__title">我的打卡记录</h2>
            <p class="panel__sub">可通过“查看全部记录”在弹窗中查看与筛选。</p>
          </div>
          <button class="btn" type="button" @click="$emit('goRecords')">查看全部记录</button>
        </div>

        <div class="list">
          <div v-for="(item, idx) in preview" :key="item.id ?? idx" class="row">
            <div class="row__k">#{{ idx + 1 }}</div>
            <div class="row__v mono">{{ item.punch_time }}</div>
          </div>
          <div v-if="recordsLoaded && preview.length === 0" class="empty">暂无记录</div>
          <div v-if="!recordsLoaded" class="empty">尚未加载记录，可先返回打卡页点击“同步记录”。</div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  user: { type: Object, required: true },
  todayRecord: { type: Object, default: null },
  latest: { type: Object, default: null },
  total: { type: Number, required: true },
  preview: { type: Array, required: true },
  recordsLoaded: { type: Boolean, required: true }
})

defineEmits(['goHome', 'goRecords', 'logout'])
</script>

<style scoped>
.wrap {
  padding: 22px 20px 32px;
  max-width: 1100px;
  margin: 0 auto;
}

.card {
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(229, 231, 235, 0.9);
  border-radius: 18px;
  box-shadow: var(--shadow-strong);
  backdrop-filter: blur(10px);
  padding: 18px;
}

.head {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 14px;
  padding-bottom: 14px;
  border-bottom: 1px dashed rgba(229, 231, 235, 0.9);
}

@media (max-width: 860px) {
  .head {
    grid-template-columns: auto 1fr;
  }
  .actions {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }
}

.avatar {
  width: 56px;
  height: 56px;
  border-radius: 18px;
  background: linear-gradient(135deg, var(--primary), var(--accent), var(--accent2));
  background-size: 200% 200%;
  animation: bgShift 10s ease-in-out infinite;
  box-shadow: var(--shadow);
}

.title {
  margin: 0;
  font-size: 20px;
  letter-spacing: 0.2px;
}

.sub {
  margin-top: 4px;
  color: var(--muted);
  font-size: 13px;
}

.actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.btn {
  border: 1px solid transparent;
  border-radius: 12px;
  padding: 10px 12px;
  font-weight: 900;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: var(--primary-ink);
}

.btn--ghost {
  background: transparent;
  border-color: rgba(229, 231, 235, 0.9);
  color: var(--text);
}

.btn--danger {
  background: linear-gradient(135deg, #ef4444, #f97316);
}

.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding: 14px 0;
}

@media (max-width: 980px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.stat {
  border: 1px solid rgba(229, 231, 235, 0.9);
  border-radius: 14px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.8);
}

.stat__k {
  font-size: 12px;
  color: var(--muted);
  font-weight: 900;
}

.stat__v {
  margin-top: 6px;
  font-weight: 900;
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

.panel {
  border: 1px solid rgba(229, 231, 235, 0.9);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.86);
  padding: 14px;
}

.panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.panel__title {
  margin: 0;
  font-size: 15px;
}

.panel__sub {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--muted);
}

.list {
  border: 1px solid rgba(229, 231, 235, 0.9);
  border-radius: 14px;
  overflow: hidden;
  background: rgba(248, 250, 252, 0.55);
}

.row {
  display: grid;
  grid-template-columns: 56px 1fr;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid rgba(229, 231, 235, 0.9);
}

.row:last-child {
  border-bottom: 0;
}

.row__k {
  color: var(--muted);
  font-weight: 900;
}

.row__v {
  font-weight: 800;
}

.empty {
  padding: 14px 12px;
  text-align: center;
  color: var(--muted);
  font-size: 13px;
}
</style>
