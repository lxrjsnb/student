<template>
  <nav class="nav" aria-label="主导航">
    <button class="item" :class="{ active: current === 'home' }" type="button" @click="$emit('navigate', 'home')">
      <span class="icon" aria-hidden="true">👆</span>
      <span class="text">打卡</span>
    </button>
    <button class="item" :class="{ active: current === 'activities' }" type="button" @click="$emit('navigate', 'activities')">
      <span class="icon" aria-hidden="true">🗓️</span>
      <span class="text">活动</span>
    </button>
    <button class="item" :class="{ active: current === 'profile' }" type="button" @click="$emit('navigate', 'profile')">
      <span class="icon" aria-hidden="true">👤</span>
      <span class="text">我的</span>
    </button>
  </nav>
</template>

<script setup>
defineProps({
  current: { type: String, required: true }
})

defineEmits(['navigate'])
</script>

<style scoped>
.nav {
  position: fixed;
  left: 12px;
  right: 12px;
  bottom: 12px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 10px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.66);
  border: 1px solid rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.14);
  z-index: 20;
}

.item {
  appearance: none;
  border: 0;
  border-radius: 14px;
  padding: 10px 8px;
  background: transparent;
  display: grid;
  justify-items: center;
  gap: 4px;
  color: rgba(15, 23, 42, 0.75);
  transition: transform 0.15s ease, background 0.15s ease, color 0.15s ease;
}

.item:hover {
  transform: translateY(-1px);
  background: rgba(0, 168, 204, 0.08);
}

.item.active {
  background: rgba(0, 168, 204, 0.14);
  color: rgba(0, 95, 120, 1);
}

.icon {
  font-size: 18px;
  line-height: 1;
}

.text {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.2px;
}
</style>

