<template>
  <section class="page">
    <header class="hero">
      <div class="hero-main">
        <div class="avatar" aria-hidden="true">
          <img v-if="user?.avatar" class="avatar-img" :src="user.avatar" alt="头像" />
          <span v-else>{{ user?.username?.charAt(0)?.toUpperCase() || '?' }}</span>
        </div>

        <div class="hero-copy">
          <p class="eyebrow">Personal Workspace</p>
          <h2 class="title">{{ user?.nickname || user?.username }}</h2>
          <p class="subtitle">{{ isAdmin ? '管理员账号' : '普通用户账号' }} · 个人数据与账户设置中心</p>
        </div>
      </div>
    </header>

    <section class="stats-grid">
      <article class="stat-card">
        <span class="stat-label">累计记录</span>
        <strong class="stat-value">{{ totalRecords }}</strong>
      </article>
      <article class="stat-card">
        <span class="stat-label">今日有效打卡</span>
        <strong class="stat-value">{{ todayCount }}</strong>
      </article>
      <article class="stat-card">
        <span class="stat-label">最近一次</span>
        <strong class="stat-value stat-value--small">{{ latestLabel }}</strong>
      </article>
    </section>

    <section class="action-card">
      <div class="action-row">
        <div>
          <p class="action-kicker">Account</p>
          <h3>管理资料、历史记录与退出</h3>
        </div>
      </div>

      <div class="actions">
        <button class="btn btn--primary" type="button" @click="$emit('openSettings')">账户设置</button>
        <button class="btn btn--ghost" type="button" @click="$emit('openHistory')">查看历史</button>
        <button class="btn btn--danger" type="button" @click="$emit('logout')">退出登录</button>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  user: { type: Object, default: null },
  totalRecords: { type: Number, default: 0 },
  todayCount: { type: Number, default: 0 },
  latestRecord: { type: Object, default: null },
  refreshing: { type: Boolean, default: false }
})

defineEmits(['openHistory', 'openSettings', 'logout', 'refresh'])

const isAdmin = computed(() => ['admin', 'super_admin'].includes(props.user?.role || ''))

const latestLabel = computed(() => {
  const raw = props.latestRecord?.punch_time
  if (!raw) return '暂无'
  return String(raw).replace('T', ' ').slice(0, 16)
})
</script>

<style scoped>
.page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 32px 18px 120px;
}

.hero {
  border-radius: 34px;
  padding: 26px;
  background:
    linear-gradient(145deg, rgba(24, 59, 77, 0.96), rgba(39, 63, 78, 0.94)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.06), transparent);
  color: #f8f4ec;
  box-shadow: 0 28px 90px rgba(20, 29, 41, 0.16);
}

.hero-main {
  display: flex;
  align-items: center;
  gap: 18px;
}

.avatar {
  width: 88px;
  height: 88px;
  border-radius: 28px;
  overflow: hidden;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, #e2c58f, #b78b4a);
  color: #152131;
  font-size: 32px;
  font-weight: 900;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.48);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(248, 244, 236, 0.62);
  font-weight: 800;
}

.title {
  margin: 0;
  font-size: clamp(30px, 4vw, 50px);
  line-height: 1;
  letter-spacing: -0.05em;
}

.subtitle {
  margin: 10px 0 0;
  color: rgba(248, 244, 236, 0.7);
  font-size: 14px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-top: 18px;
}

.stat-card,
.action-card {
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(24, 33, 47, 0.08);
  box-shadow: 0 24px 64px rgba(20, 29, 41, 0.08);
}

.stat-card {
  min-height: 148px;
  padding: 22px;
  display: grid;
  align-content: space-between;
}

.stat-label,
.action-kicker {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(24, 59, 77, 0.54);
}

.stat-value {
  font-size: 42px;
  line-height: 0.98;
  letter-spacing: -0.06em;
  color: #152131;
}

.stat-value--small {
  font-size: 24px;
}

.action-card {
  margin-top: 18px;
  padding: 24px;
}

.action-row h3 {
  margin: 8px 0 0;
  font-size: 32px;
  line-height: 1.04;
  letter-spacing: -0.05em;
  color: #152131;
}

.actions {
  margin-top: 22px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.btn {
  min-height: 58px;
  border-radius: 18px;
  border: 0;
  font-size: 14px;
  font-weight: 800;
  transition: transform 0.16s ease, box-shadow 0.16s ease, filter 0.16s ease;
}

.btn:hover {
  transform: translateY(-1px);
}

.btn--primary {
  background: linear-gradient(135deg, #183b4d, #29546c);
  color: #f8f4ec;
  box-shadow: 0 18px 30px rgba(24, 59, 77, 0.18);
}

.btn--ghost {
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
}

.btn--danger {
  background: rgba(154, 47, 39, 0.1);
  color: #9a2f27;
}

@media (max-width: 760px) {
  .hero-main {
    align-items: flex-start;
    flex-direction: column;
  }

  .stats-grid,
  .actions {
    grid-template-columns: 1fr;
  }
}
</style>
