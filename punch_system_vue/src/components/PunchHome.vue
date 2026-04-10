<template>
  <section class="home">
    <header class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Daily Console</p>
        <h1 class="title">下午好，{{ displayName }}</h1>
        <p class="subtitle">把今天的完成感留在系统里，状态会比口号更有说服力。</p>
      </div>

      <div class="quick-actions" role="group" aria-label="快捷入口">
        <button class="quick-btn" type="button" @click="$emit('openHistory')">
          <ClockIcon />
          <span>历史记录</span>
        </button>
        <button class="quick-btn" type="button" @click="$emit('openMessages')">
          <span v-if="pendingApproval" class="dot" aria-hidden="true"></span>
          <MessageIcon />
          <span>审批消息</span>
        </button>
      </div>
    </header>

    <div class="surface">
      <section class="spotlight">
        <div class="status-strip">
          <div class="status-card">
            <span class="status-label">当前状态</span>
            <strong class="status-value">{{ pendingApproval ? '待审批中' : '可立即打卡' }}</strong>
          </div>
          <div class="status-card">
            <span class="status-label">待处理记录</span>
            <strong class="status-value">{{ pendingCount }}</strong>
          </div>
        </div>

        <div v-if="pendingApproval" class="pending-tip" role="status" aria-live="polite">
          你有 {{ pendingCount }} 条记录正在等待管理员处理，可在“审批消息”里查看状态或发起催办。
        </div>

        <div class="punch-stage">
          <div class="stage-copy">
            <p class="stage-kicker">One Tap Check-In</p>
            <h2 class="stage-title">一次提交，完成今天的留痕。</h2>
            <p class="stage-text">系统会保留你的有效记录，并在审批完成后进入历史日历。</p>
          </div>

          <button class="punch" type="button" :disabled="disabled" @click="$emit('punch')">
            <span class="punch-ring"></span>
            <span class="punch-label">
              {{
                cooldownRemaining > 0
                  ? `${cooldownRemaining}s`
                  : loading
                    ? '提交中'
                    : '立即打卡'
              }}
            </span>
            <span class="punch-sub">Tap to confirm</span>
          </button>
        </div>

        <div v-if="message" class="msg" :class="`msg--${messageType}`">
          {{ message }}
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import ClockIcon from './ClockIcon.vue'
import MessageIcon from './MessageIcon.vue'

const props = defineProps({
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

const displayName = computed(() => props.user?.nickname || props.user?.username || '用户')
</script>

<style scoped>
.home {
  padding: 32px 18px 120px;
  max-width: 1120px;
  margin: 0 auto;
}

.hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 22px;
}

.eyebrow,
.stage-kicker {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(24, 59, 77, 0.58);
}

.title {
  margin: 0;
  font-size: clamp(34px, 4vw, 58px);
  line-height: 0.98;
  letter-spacing: -0.05em;
  color: #152131;
}

.subtitle {
  margin: 14px 0 0;
  max-width: 540px;
  color: rgba(24, 33, 47, 0.62);
  font-size: 15px;
  line-height: 1.8;
}

.quick-actions {
  display: flex;
  gap: 12px;
}

.quick-btn {
  position: relative;
  min-width: 132px;
  min-height: 72px;
  border: 1px solid rgba(24, 33, 47, 0.08);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.68);
  box-shadow: 0 20px 40px rgba(20, 29, 41, 0.08);
  display: grid;
  justify-items: center;
  align-content: center;
  gap: 8px;
  color: #183b4d;
  font-weight: 800;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.quick-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 24px 46px rgba(20, 29, 41, 0.12);
}

.quick-btn :deep(.icon) {
  width: 18px;
  height: 18px;
}

.quick-btn span:last-child {
  font-size: 13px;
}

.dot {
  position: absolute;
  top: 16px;
  right: 18px;
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: #c44a3a;
  box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.95);
}

.surface {
  border-radius: 36px;
  padding: 18px;
  border: 1px solid rgba(24, 33, 47, 0.06);
  background: rgba(255, 255, 255, 0.28);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.spotlight {
  border-radius: 30px;
  padding: 28px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.86), rgba(248, 242, 231, 0.72)),
    linear-gradient(135deg, rgba(24, 59, 77, 0.12), transparent 56%);
  box-shadow: 0 24px 64px rgba(20, 29, 41, 0.1);
}

.status-strip {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.status-card {
  min-height: 96px;
  padding: 18px 20px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(24, 33, 47, 0.08);
  display: grid;
  align-content: space-between;
}

.status-label {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(24, 59, 77, 0.48);
  font-weight: 800;
}

.status-value {
  font-size: 28px;
  line-height: 1.05;
  letter-spacing: -0.04em;
  color: #152131;
}

.pending-tip {
  margin-top: 16px;
  padding: 16px 18px;
  border-radius: 22px;
  background: rgba(191, 133, 36, 0.12);
  border: 1px solid rgba(191, 133, 36, 0.16);
  color: #84581c;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.7;
}

.punch-stage {
  margin-top: 18px;
  min-height: 420px;
  border-radius: 30px;
  padding: 26px;
  background:
    radial-gradient(circle at 50% 38%, rgba(255, 255, 255, 0.42), transparent 24%),
    linear-gradient(180deg, rgba(24, 59, 77, 0.96), rgba(14, 28, 42, 0.98));
  color: #f8f4ec;
  display: grid;
  align-items: center;
  justify-items: center;
  text-align: center;
  overflow: hidden;
  position: relative;
}

.punch-stage::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 50% 36%, rgba(215, 177, 120, 0.16), transparent 18%),
    radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.08), transparent 22%),
    radial-gradient(circle at 82% 18%, rgba(109, 139, 116, 0.16), transparent 18%);
  pointer-events: none;
}

.stage-copy,
.punch {
  position: relative;
  z-index: 1;
}

.stage-title {
  margin: 0;
  font-size: clamp(30px, 3vw, 44px);
  line-height: 1.02;
  letter-spacing: -0.05em;
}

.stage-text {
  margin: 14px auto 0;
  max-width: 480px;
  color: rgba(248, 244, 236, 0.72);
  font-size: 15px;
  line-height: 1.8;
}

.punch {
  margin-top: 28px;
  width: 256px;
  height: 256px;
  border-radius: 999px;
  border: 0;
  background:
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.14) 34%, transparent 35%),
    linear-gradient(145deg, #e6c58d, #b78b4a 60%, #8f6a34 100%);
  color: #152131;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.6),
    0 30px 48px rgba(0, 0, 0, 0.26);
  display: grid;
  place-items: center;
  align-content: center;
  gap: 6px;
  position: relative;
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
}

.punch:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.01);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.72),
    0 36px 58px rgba(0, 0, 0, 0.3);
  filter: saturate(1.06);
}

.punch:disabled {
  opacity: 0.68;
  cursor: not-allowed;
  box-shadow: none;
}

.punch-ring {
  position: absolute;
  inset: 18px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.34);
}

.punch-label {
  font-size: 28px;
  letter-spacing: 0.06em;
  font-weight: 900;
}

.punch-sub {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: rgba(24, 33, 47, 0.62);
  font-weight: 800;
}

.msg {
  margin-top: 16px;
  padding: 16px 18px;
  border-radius: 20px;
  border: 1px solid transparent;
  font-size: 14px;
  font-weight: 700;
}

.msg--success {
  background: rgba(17, 97, 73, 0.1);
  color: #116149;
  border-color: rgba(17, 97, 73, 0.16);
}

.msg--error {
  background: rgba(154, 47, 39, 0.1);
  color: #9a2f27;
  border-color: rgba(154, 47, 39, 0.16);
}

.msg--warn {
  background: rgba(132, 88, 28, 0.1);
  color: #84581c;
  border-color: rgba(132, 88, 28, 0.16);
}

.msg--info {
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
  border-color: rgba(24, 59, 77, 0.12);
}

@media (max-width: 760px) {
  .hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .quick-actions {
    width: 100%;
  }

  .quick-btn {
    flex: 1;
    min-width: 0;
  }

  .status-strip {
    grid-template-columns: 1fr;
  }

  .punch {
    width: 216px;
    height: 216px;
  }
}
</style>
