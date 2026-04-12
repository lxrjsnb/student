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
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  max-width: 520px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  padding: 10px 14px calc(10px + env(safe-area-inset-bottom, 0px));
  border-radius: 22px 22px 0 0;
  background: rgba(250, 247, 241, 0.88);
  border: 1px solid rgba(24, 33, 47, 0.08);
  border-bottom: 0;
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow: 0 -8px 28px rgba(52, 71, 97, 0.1);
  z-index: 40;
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
  color: rgba(24, 59, 77, 0.46);
  transition: transform 0.15s ease, background 0.15s ease, color 0.15s ease;
}

.item:hover {
  transform: translateY(-1px);
}

.item.active {
  background: rgba(215, 177, 120, 0.18);
  color: #183b4d;
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

@media (min-width: 769px) {
  .nav {
    left: 50%;
    right: auto;
    bottom: 18px;
    width: min(520px, calc(100vw - 28px));
    margin: 0;
    transform: translateX(-50%);
    padding: 10px;
    border-radius: 24px;
    border-bottom: 1px solid rgba(24, 33, 47, 0.08);
    box-shadow: 0 24px 52px rgba(52, 71, 97, 0.12);
  }
}
</style>
