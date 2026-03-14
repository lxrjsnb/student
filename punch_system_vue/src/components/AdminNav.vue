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
  left: 50%;
  bottom: 18px;
  transform: translateX(-50%);
  width: min(520px, calc(100% - 24px));
  padding: 10px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.14);
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
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
  color: rgba(15, 23, 42, 0.78);
}

.adminNav__item--active {
  background: rgba(0, 168, 204, 0.12);
  border: 1px solid rgba(0, 168, 204, 0.18);
  color: rgba(0, 95, 120, 1);
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
</style>

