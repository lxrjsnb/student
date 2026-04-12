<template>
  <nav class="adminNav" role="navigation" aria-label="管理员导航">
    <button
      v-for="item in items"
      :key="item.key"
      class="adminNav__item"
      :class="{ 'adminNav__item--active': current === item.key }"
      type="button"
      @click="$emit('navigate', item.key)"
    >
      <span class="adminNav__icon" aria-hidden="true">{{ item.icon }}</span>
      <span class="adminNav__text">{{ item.label }}</span>
    </button>
  </nav>
</template>

<script setup>
defineProps({
  current: { type: String, default: '' }
})

defineEmits(['navigate'])

const items = [
  { key: 'adminPunchApproval', label: '审批', icon: '✅' },
  { key: 'adminActivityUpload', label: '活动', icon: '🖼️' },
  { key: 'adminProfile', label: '我的', icon: '👤' }
]
</script>

<style scoped>
.adminNav {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  max-width: 520px;
  margin: 0 auto;
  padding: 10px 14px calc(10px + env(safe-area-inset-bottom, 0px));
  border-radius: 18px 18px 0 0;
  background: rgba(250, 247, 241, 0.88);
  border: 1px solid rgba(24, 33, 47, 0.08);
  border-bottom: 0;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: 0 -8px 28px rgba(52, 71, 97, 0.1);
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  z-index: 40;
}

.adminNav__item {
  border: 0;
  background: transparent;
  border-radius: 14px;
  padding: 10px 8px;
  display: grid;
  place-items: center;
  gap: 4px;
  cursor: pointer;
  color: rgba(24, 59, 77, 0.52);
}

.adminNav__item--active {
  background: rgba(109, 139, 116, 0.16);
  border: 1px solid rgba(109, 139, 116, 0.16);
  color: #183b4d;
}

.adminNav__icon {
  font-size: 18px;
  line-height: 1;
}

.adminNav__text {
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.2px;
}

@media (min-width: 769px) {
  .adminNav {
    left: 50%;
    right: auto;
    bottom: 18px;
    width: min(520px, calc(100% - 24px));
    margin: 0;
    transform: translateX(-50%);
    padding: 10px;
    border-radius: 18px;
    border-bottom: 1px solid rgba(24, 33, 47, 0.08);
    box-shadow: 0 18px 44px rgba(52, 71, 97, 0.12);
  }
}
</style>
