<template>
  <header class="header">
    <div class="header__inner">
      <div class="brand">
        <div class="brand__mark" aria-hidden="true">打</div>
        <div class="brand__meta">
          <div class="brand__title">打卡系统</div>
          <div class="brand__sub">规范化考勤 / 打卡记录</div>
        </div>
      </div>

      <div class="header__right">
        <nav class="nav" aria-label="页面导航">
          <button
            class="nav__btn"
            type="button"
            :class="{ 'nav__btn--active': view === 'home' }"
            :disabled="disabled"
            @click="$emit('goHome')"
          >
            打卡
          </button>
          <button
            class="nav__btn"
            type="button"
            :class="{ 'nav__btn--active': view === 'profile' }"
            :disabled="disabled"
            @click="$emit('goProfile')"
          >
            个人
          </button>
        </nav>

        <div class="now" :title="nowText">{{ nowText }}</div>
        <div v-if="user" class="user">
          <span class="user__name">{{ user.username }}</span>
          <span class="user__id">ID: {{ user.id }}</span>
          <button class="btn btn--ghost" type="button" @click="$emit('logout')">
            退出
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
defineProps({
  user: { type: Object, default: null },
  nowText: { type: String, required: true },
  view: { type: String, required: true },
  disabled: { type: Boolean, default: false }
})

defineEmits(['logout', 'goHome', 'goProfile'])
</script>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: rgba(246, 247, 251, 0.85);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
}

.header::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 2px;
  background: linear-gradient(90deg, rgba(37, 99, 235, 0.85), rgba(124, 58, 237, 0.8), rgba(6, 182, 212, 0.75), rgba(249, 115, 22, 0.75));
  background-size: 200% 100%;
  animation: bgShift 10s ease-in-out infinite;
  opacity: 0.65;
  pointer-events: none;
}

.header__inner {
  max-width: 1100px;
  margin: 0 auto;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand__mark {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  color: var(--primary-ink);
  background: linear-gradient(135deg, var(--primary), var(--accent), var(--accent2));
  background-size: 200% 200%;
  animation: bgShift 10s ease-in-out infinite;
  font-weight: 950;
  box-shadow: var(--shadow);
}

.brand__title {
  font-weight: 800;
  letter-spacing: 0.2px;
}

.brand__sub {
  font-size: 12px;
  color: var(--muted);
}

.header__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav {
  display: inline-flex;
  gap: 6px;
  padding: 6px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(10px);
}

.nav__btn {
  border: 1px solid transparent;
  border-radius: 999px;
  padding: 8px 12px;
  font-weight: 900;
  font-size: 13px;
  background: transparent;
  color: var(--text);
  transition: background 0.18s ease, transform 0.18s ease, filter 0.18s ease;
}

.nav__btn:hover {
  background: rgba(37, 99, 235, 0.08);
  transform: translateY(-1px);
  filter: saturate(1.08);
}

.nav__btn--active {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.2), rgba(124, 58, 237, 0.18));
  border-color: rgba(37, 99, 235, 0.25);
}

.nav__btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.now {
  font-size: 12px;
  color: var(--muted);
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--panel);
}

.user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--panel);
}

.user__name {
  font-weight: 700;
}

.user__id {
  font-size: 12px;
  color: var(--muted);
}

.btn {
  border: 1px solid transparent;
  border-radius: 10px;
  padding: 8px 12px;
  font-weight: 700;
  background: var(--primary);
  color: var(--primary-ink);
  transition: transform 0.16s ease, filter 0.16s ease;
}

.btn:hover {
  transform: translateY(-1px);
  filter: saturate(1.1);
}

.btn:active {
  transform: translateY(0);
}

.btn--ghost {
  background: rgba(255, 255, 255, 0.55);
  border-color: rgba(229, 231, 235, 0.9);
  color: var(--text);
}

.btn--ghost:hover {
  border-color: rgba(203, 213, 225, 0.95);
}
</style>
