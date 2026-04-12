<template>
  <section class="page">
    <header class="hero">
      <div class="heroTop">
        <div class="avatar" aria-hidden="true">
          <img v-if="user?.avatar" class="avatarImg" :src="user.avatar" alt="头像" />
          <span v-else>{{ displayInitial }}</span>
        </div>

        <div class="heroCopy">
          <p class="eyebrow">Profile</p>
          <h2 class="title">
            {{ user?.nickname || user?.username }}
            <span class="roleInline">{{ roleText }}</span>
          </h2>
          <p class="subtitle">{{ studentNoText }}</p>
        </div>
      </div>

      <div class="heroMeta">
        <span class="metaPill">phone {{ phoneText }}</span>
        <span class="metaPill">department {{ departmentText }}</span>
      </div>
    </header>

    <section class="panel">
      <div class="panelHead">
        <div>
          <p class="panelKicker">Workspace</p>
          <h3 class="panelTitle">我的</h3>
        </div>
      </div>

      <div class="actionList">
        <button class="actionRow" type="button" @click="$emit('openSettings')">
          <div class="actionMain">
            <span class="actionTitle">账户设置</span>
            <span class="actionDesc">修改账号、头像和密码</span>
          </div>
          <span class="actionArrow" aria-hidden="true">›</span>
        </button>

        <button class="actionRow" type="button" @click="$emit('openHistory')">
          <div class="actionMain">
            <span class="actionTitle">历史记录</span>
            <span class="actionDesc">查看月历和过往打卡明细</span>
          </div>
          <span class="actionArrow" aria-hidden="true">›</span>
        </button>

        <button class="actionRow actionRow--danger" type="button" @click="$emit('logout')">
          <div class="actionMain">
            <span class="actionTitle">退出登录</span>
            <span class="actionDesc">清除当前登录状态并返回首页</span>
          </div>
          <span class="actionState actionState--danger">退出</span>
        </button>
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

const displayInitial = computed(() => {
  const value = props.user?.nickname || props.user?.username || '?'
  return String(value).charAt(0).toUpperCase()
})

const roleText = computed(() => {
  if (props.user?.role === 'super_admin') return '主席'
  if (props.user?.role === 'admin') return '部长'
  return '部员'
})

const phoneText = computed(() => props.user?.phone || '-')
const departmentText = computed(() => props.user?.department || '-')
const studentNoText = computed(() => props.user?.studentNo || '-')
</script>

<style scoped>
.page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 32px 18px 120px;
}

.hero {
  padding: 24px;
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(24, 33, 47, 0.08);
  box-shadow: 0 22px 54px rgba(20, 29, 41, 0.08);
}

.heroTop {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar {
  width: 78px;
  height: 78px;
  border-radius: 24px;
  overflow: hidden;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, #e2c58f, #b78b4a);
  color: #152131;
  font-size: 28px;
  font-weight: 900;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42);
}

.avatarImg {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.heroCopy {
  min-width: 0;
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

.title {
  margin: 8px 0 0;
  font-size: clamp(30px, 4vw, 46px);
  line-height: 1;
  letter-spacing: -0.05em;
  color: #152131;
}

.roleInline {
  margin-left: 10px;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: rgba(24, 59, 77, 0.64);
}

.subtitle {
  margin: 8px 0 0;
  color: rgba(24, 33, 47, 0.62);
  font-size: 14px;
}

.heroMeta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.metaPill {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
  font-size: 12px;
  font-weight: 700;
}

.panel {
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(24, 33, 47, 0.08);
  box-shadow: 0 20px 48px rgba(20, 29, 41, 0.06);
}

.panel {
  margin-top: 18px;
  padding: 22px;
}

.panelHead {
  margin-bottom: 16px;
}

.panelTitle {
  margin: 8px 0 0;
  font-size: 30px;
  line-height: 1.04;
  letter-spacing: -0.05em;
  color: #152131;
}

.actionList {
  display: grid;
  gap: 10px;
}

.actionRow {
  width: 100%;
  border: 0;
  border-radius: 22px;
  padding: 16px 18px;
  background: rgba(248, 242, 231, 0.66);
  border: 1px solid rgba(24, 33, 47, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  text-align: left;
  transition: transform 0.16s ease, background 0.16s ease;
}

.actionRow:hover {
  transform: translateY(-1px);
  background: rgba(248, 242, 231, 0.88);
}

.actionRow--danger {
  background: rgba(154, 47, 39, 0.08);
  border-color: rgba(154, 47, 39, 0.08);
}

.actionMain {
  min-width: 0;
  display: grid;
  gap: 6px;
}

.actionTitle {
  font-size: 16px;
  font-weight: 800;
  color: #152131;
}

.actionDesc {
  color: rgba(24, 33, 47, 0.62);
  font-size: 13px;
  line-height: 1.6;
}

.actionArrow,
.actionState {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
  font-size: 12px;
  font-weight: 800;
}

.actionArrow {
  width: 34px;
  padding: 0;
  font-size: 22px;
  line-height: 1;
}

.actionState--danger {
  background: rgba(154, 47, 39, 0.12);
  color: #9a2f27;
}

@media (max-width: 900px) {
  .statsGrid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .heroTop {
    align-items: flex-start;
  }

  .statsGrid {
    grid-template-columns: 1fr;
  }

  .actionRow {
    padding: 16px;
  }

  .actionState,
  .actionArrow {
    min-height: 32px;
  }
}
</style>
