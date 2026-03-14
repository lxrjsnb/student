<template>
  <section class="home">
    <div class="topActions" role="group" aria-label="快捷入口">
      <button class="topBtn" type="button" @click="$emit('openHistory')" aria-label="历史打卡" title="历史打卡">
        <ClockIcon />
      </button>
      <button class="topBtn" type="button" @click="$emit('openMessages')" aria-label="打卡消息" title="打卡消息">
        <span v-if="pendingApproval" class="dot" aria-hidden="true"></span>
        <MessageIcon />
      </button>
    </div>

    <header class="hero">
      <p class="kicker">今天也要好好生活</p>
      <p class="name">Hi，{{ user?.username }}</p>
    </header>

    <div class="center">
      <div v-if="pendingApproval" class="pendingTip" role="status" aria-live="polite">
        {{ pendingCount }}条记录已提交管理员，待审批中
      </div>

      <button class="punch" type="button" :disabled="disabled" @click="$emit('punch')">
        <span class="punchInner">
          <span class="punchText">
            {{
              cooldownRemaining > 0
                ? `${cooldownRemaining}s`
                : loading
                  ? '…'
                  : '打卡'
            }}
          </span>
        </span>
      </button>

      <div v-if="message" class="msg" :class="`msg--${messageType}`">
        {{ message }}
      </div>
    </div>
  </section>
</template>

<script setup>
import ClockIcon from './ClockIcon.vue'
import MessageIcon from './MessageIcon.vue'

defineProps({
  user: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  cooldownRemaining: { type: Number, default: 0 },
  pendingApproval: { type: Boolean, default: false },
  pendingCount: { type: Number, default: 0 },
  message: { type: String, default: '' },
  messageType: { type: String, default: 'info' }
})

defineEmits(['punch', 'openHistory', 'openMessages'])
</script>

<style scoped>
.home {
  padding: 18px 16px 92px;
  max-width: 520px;
  margin: 0 auto;
  min-height: calc(100vh - 92px);
  position: relative;
  display: flex;
  flex-direction: column;
}

.topActions {
  position: fixed;
  top: calc(14px + env(safe-area-inset-top, 0px));
  left: calc(14px + env(safe-area-inset-left, 0px));
  display: inline-flex;
  align-items: center;
  gap: 10px;
  z-index: 30;
}

.topBtn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  border-radius: 999px;
  border: 0;
  background: transparent;
  color: rgba(0, 95, 120, 0.9);
  opacity: 0.85;
  transition: transform 0.15s ease, opacity 0.15s ease, filter 0.15s ease;
}

.topBtn:hover {
  opacity: 1;
  transform: translateY(-1px);
  filter: drop-shadow(0 10px 18px rgba(0, 95, 120, 0.18));
}

.topBtn:active {
  transform: translateY(0);
}

.topBtn :deep(.icon) {
  width: 18px;
  height: 18px;
}

.dot {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #ef4444;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.9);
}

.kicker {
  margin: 0;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.6);
  text-align: center;
}

.name {
  margin: 4px 0 0;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.2px;
  color: rgba(15, 23, 42, 0.9);
  text-align: center;
}

.hero {
  padding-top: 60px;
  padding-bottom: 18px;
}

.center {
  flex: 1;
  display: grid;
  place-items: center;
  gap: 14px;
  padding-bottom: 24px;
}

.pendingTip {
  width: 100%;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid rgba(234, 179, 8, 0.28);
  background: rgba(234, 179, 8, 0.12);
  color: rgba(133, 77, 14, 0.95);
  font-size: 13px;
  font-weight: 800;
  text-align: center;
}

.punch {
  border: 0;
  width: 168px;
  height: 168px;
  border-radius: 999px;
  background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.36), transparent 42%),
    linear-gradient(135deg, rgba(0, 168, 204, 0.96), rgba(0, 139, 168, 0.96));
  color: white;
  font-weight: 900;
  font-size: 16px;
  display: grid;
  place-items: center;
  box-shadow: 0 18px 34px rgba(0, 168, 204, 0.28);
  transition: transform 0.16s ease, box-shadow 0.16s ease, filter 0.16s ease;
  position: relative;
  overflow: hidden;
}

.punch::before {
  content: '';
  position: absolute;
  inset: -55%;
  background:
    radial-gradient(circle at 35% 35%, rgba(255, 255, 255, 0.3), transparent 40%),
    radial-gradient(circle at 70% 65%, rgba(255, 255, 255, 0.22), transparent 46%),
    radial-gradient(circle at 45% 80%, rgba(255, 241, 138, 0.22), transparent 56%),
    repeating-linear-gradient(45deg, rgba(255, 255, 255, 0.14) 0 10px, transparent 10px 24px);
  transform: rotate(6deg);
}

.punch > * {
  position: relative;
}

.punchInner {
  display: grid;
  gap: 8px;
  justify-items: center;
}

.punch:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 22px 40px rgba(0, 168, 204, 0.32);
  filter: saturate(1.05);
}

.punch:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

.punchText {
  font-size: 20px;
  font-weight: 1000;
  letter-spacing: 0.28em;
  text-indent: 0.28em;
  text-shadow: 0 10px 24px rgba(2, 132, 199, 0.35);
  line-height: 1;
}

.msg {
  width: 100%;
  font-size: 13px;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.66);
}

.msg--success {
  background: rgba(34, 197, 94, 0.12);
  color: #15803d;
  border-color: rgba(34, 197, 94, 0.25);
}

.msg--error {
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
  border-color: rgba(239, 68, 68, 0.25);
}

.msg--warn {
  background: rgba(245, 158, 11, 0.12);
  color: #b45309;
  border-color: rgba(245, 158, 11, 0.25);
}

.msg--info {
  background: rgba(0, 168, 204, 0.12);
  color: #008ba8;
  border-color: rgba(0, 168, 204, 0.25);
}

@media (max-width: 420px) {
  .punch {
    width: 152px;
    height: 152px;
  }
}
</style>
