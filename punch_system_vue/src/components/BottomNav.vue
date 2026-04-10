<template>
  <nav class="nav" aria-label="主导航">
    <button class="item" :class="{ active: current === 'home' }" type="button" @click="$emit('navigate', 'home')">
      <span class="icon" aria-hidden="true">●</span>
      <span class="text">打卡台</span>
    </button>
    <button class="item" :class="{ active: current === 'activities' }" type="button" @click="$emit('navigate', 'activities')">
      <span class="icon" aria-hidden="true">◆</span>
      <span class="text">活动库</span>
    </button>
    <button class="item" :class="{ active: current === 'profile' }" type="button" @click="$emit('navigate', 'profile')">
      <span class="icon" aria-hidden="true">◌</span>
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
  left: 50%;
  bottom: 18px;
  transform: translateX(-50%);
  width: min(520px, calc(100vw - 28px));
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  padding: 10px;
  border-radius: 24px;
  background: rgba(18, 32, 51, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow: 0 24px 70px rgba(20, 29, 41, 0.24);
  z-index: 30;
}

.item {
  appearance: none;
  border: 0;
  border-radius: 18px;
  min-height: 60px;
  background: transparent;
  display: grid;
  justify-items: center;
  align-content: center;
  gap: 6px;
  color: rgba(248, 244, 236, 0.56);
  transition: transform 0.15s ease, background 0.15s ease, color 0.15s ease;
}

.item:hover {
  transform: translateY(-1px);
}

.item.active {
  background: rgba(255, 255, 255, 0.08);
  color: #f8f4ec;
}

.icon {
  font-size: 12px;
  letter-spacing: 0.2em;
}

.text {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
}
</style>
