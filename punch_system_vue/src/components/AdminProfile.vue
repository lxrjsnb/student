<template>
  <section class="page">
    <header class="head">
      <div>
        <p class="kicker">管理员</p>
        <h2 class="title">个人中心</h2>
      </div>
    </header>

    <div class="card">
      <div class="user">
        <div class="avatar" aria-hidden="true">
          <span>{{ displayInitial }}</span>
        </div>
        <div class="uMeta">
          <p class="uName">
            {{ user?.username }}
            <span class="tag">管理员</span>
          </p>
          <p class="uSub">角色：{{ roleText }}</p>
        </div>
      </div>

      <div class="actions">
        <button v-if="user?.role === 'super_admin'" class="btn ghost" type="button" @click="$emit('goSuperAdmin')">
          超级管理员控制台
        </button>
        <button class="btn danger" type="button" @click="$emit('logout')">退出登录</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  user: { type: Object, default: null }
})

defineEmits(['logout', 'goSuperAdmin'])

const roleText = computed(() => {
  if (props.user?.role === 'super_admin') return '超级管理员'
  return '管理员'
})

const displayInitial = computed(() => props.user?.username?.charAt(0)?.toUpperCase?.() || '?')
</script>

<style scoped>
.page {
  padding: 18px 16px 92px;
  width: 100%;
}

.head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
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

.card {
  width: 100%;
  max-width: 420px;
  margin: 0 auto;
  border-radius: 20px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.66);
  border: 1px solid rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.14);
}

.user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 52px;
  height: 52px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  font-weight: 1000;
  color: rgba(0, 95, 120, 1);
  background: linear-gradient(135deg, rgba(0, 168, 204, 0.18), rgba(254, 214, 227, 0.4));
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.uName {
  margin: 0;
  font-weight: 1000;
  color: rgba(15, 23, 42, 0.9);
  letter-spacing: 0.2px;
  display: flex;
  gap: 10px;
  align-items: center;
}

.tag {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(0, 168, 204, 0.12);
  border: 1px solid rgba(0, 168, 204, 0.18);
  color: rgba(0, 95, 120, 1);
}

.uSub {
  margin: 6px 0 0;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.6);
}

.actions {
  margin-top: 14px;
  display: grid;
  gap: 10px;
}

.btn {
  width: 100%;
  border: 0;
  border-radius: 16px;
  padding: 12px 14px;
  font-weight: 900;
}

.ghost {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.06);
  color: rgba(15, 23, 42, 0.78);
}

.danger {
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.22);
  color: #b91c1c;
}
</style>

