<template>
  <teleport to="body">
    <div v-if="open" class="overlay" role="presentation" @mousedown.self="emit('close')">
      <section
        class="dialog"
        role="dialog"
        aria-modal="true"
        :aria-label="title || '弹窗'"
        tabindex="-1"
        ref="dialogEl"
      >
        <header class="head">
          <div class="title">
            <div class="title__h">{{ title }}</div>
            <div v-if="subtitle" class="title__s">{{ subtitle }}</div>
          </div>
          <button class="btn btn--ghost btn--icon" type="button" @click="emit('close')" aria-label="关闭">
            <span aria-hidden="true">×</span>
          </button>
        </header>

        <div class="body">
          <slot />
        </div>
      </section>
    </div>
  </teleport>
</template>

<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, required: true },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' }
})

const emit = defineEmits(['close'])

const dialogEl = ref(null)

let previousOverflow = ''

function onKeydown(e) {
  if (!props.open) return
  if (e.key === 'Escape') emit('close')
}

watch(
  () => props.open,
  async (isOpen) => {
    if (isOpen) {
      previousOverflow = document.body.style.overflow
      document.body.style.overflow = 'hidden'
      window.addEventListener('keydown', onKeydown)
      await nextTick()
      dialogEl.value?.focus?.()
    } else {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', onKeydown)
    }
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  document.body.style.overflow = previousOverflow
  window.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: grid;
  place-items: center;
  padding: 18px;
  background: rgba(2, 6, 23, 0.45);
  backdrop-filter: blur(8px);
}

.dialog {
  width: min(980px, 100%);
  max-height: min(82vh, 820px);
  overflow: hidden;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  background: rgba(255, 255, 255, 0.78);
  box-shadow: var(--shadow-strong);
  backdrop-filter: blur(16px);
}

.head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 14px 10px;
  border-bottom: 1px solid rgba(229, 231, 235, 0.85);
}

.title__h {
  font-size: 15px;
  font-weight: 950;
  letter-spacing: 0.2px;
}

.title__s {
  margin-top: 2px;
  font-size: 12px;
  color: var(--muted);
}

.body {
  padding: 12px;
  overflow: auto;
  max-height: calc(min(82vh, 820px) - 56px);
}

.btn {
  border: 1px solid transparent;
  border-radius: 12px;
  padding: 10px 12px;
  font-weight: 900;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: var(--primary-ink);
  transition: transform 0.16s ease, filter 0.16s ease, background 0.16s ease;
}

.btn:hover {
  transform: translateY(-1px);
  filter: saturate(1.1);
}

.btn:active {
  transform: translateY(0);
}

.btn--ghost {
  background: rgba(255, 255, 255, 0.65);
  color: var(--text);
  border-color: rgba(229, 231, 235, 0.9);
}

.btn--icon {
  width: 40px;
  height: 40px;
  padding: 0;
  display: grid;
  place-items: center;
  font-size: 22px;
  line-height: 1;
}
</style>
