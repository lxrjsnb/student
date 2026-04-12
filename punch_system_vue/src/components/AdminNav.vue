<template>
  <nav class="adminNav" :style="navStyle" role="navigation" aria-label="管理员导航">
    <button
      v-for="item in items"
      :key="item.key"
      class="adminNav__item"
      :class="{ 'adminNav__item--active': current === item.key }"
      type="button"
      @click="$emit('navigate', item.key)"
    >
      <span class="adminNav__icon" aria-hidden="true">{{ item.icon }}</span>
      <span class="adminNav__text adminNav__text--with-dot">
        {{ item.label }}
        <span v-if="item.key === 'adminProfile' && delegationAlert" class="adminNav__dot" aria-hidden="true"></span>
      </span>
    </button>
  </nav>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  role: { type: String, default: 'user' },
  delegationAlert: { type: Boolean, default: false },
  current: { type: String, default: '' }
})

defineEmits(['navigate'])

const items = computed(() => {
  const baseItems = [
    { key: 'adminPunchApproval', label: '审批', icon: '●' },
    { key: 'adminActivityUpload', label: '日常活动', icon: '◆' }
  ]
  if (props.role === 'super_admin') {
    baseItems.push({ key: 'superAdminStatus', label: '总览', icon: '◍' })
  }
  baseItems.push({ key: 'adminProfile', label: '我的', icon: '◌' })
  return baseItems
})

const navStyle = computed(() => ({
  gridTemplateColumns: `repeat(${items.value.length}, minmax(0, 1fr))`
}))
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
  display: grid;
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

.adminNav__item {
  appearance: none;
  border: 0;
  background: transparent;
  border-radius: 18px;
  min-height: 60px;
  display: grid;
  justify-items: center;
  align-content: center;
  gap: 6px;
  color: rgba(24, 59, 77, 0.46);
  transition: transform 0.15s ease, background 0.15s ease, color 0.15s ease;
}

.adminNav__item:hover {
  transform: translateY(-1px);
}

.adminNav__item--active {
  background: rgba(215, 177, 120, 0.18);
  color: #183b4d;
}

.adminNav__icon {
  font-size: 12px;
  letter-spacing: 0.2em;
}

.adminNav__text {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  white-space: nowrap;
}

.adminNav__text--with-dot {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.adminNav__dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: #d83b32;
  box-shadow: 0 0 0 4px rgba(216, 59, 50, 0.12);
}

@media (min-width: 769px) {
  .adminNav {
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
