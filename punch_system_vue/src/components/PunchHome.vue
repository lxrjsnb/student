<template>
  <section class="home">
    <header class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Daily Console</p>
        <h1 class="title">{{ greeting }}，{{ displayName }}</h1>
        <div class="quick-actions" role="group" aria-label="快捷入口">
          <button class="quick-btn" type="button" aria-label="历史记录" title="历史记录" @click="$emit('openHistory')">
            <ClockIcon />
          </button>
        <button class="quick-btn" type="button" aria-label="消息" title="消息" @click="$emit('openMessages')">
          <span v-if="pendingApproval" class="dot" aria-hidden="true"></span>
          <MessageIcon />
        </button>
        </div>
      </div>
    </header>

    <section class="punch-stage">
      <div class="scene" aria-hidden="true">
        <span class="scene-sun"></span>
        <span class="scene-cloud scene-cloud--left"></span>
        <span class="scene-cloud scene-cloud--right"></span>
        <span class="scene-hill scene-hill--back"></span>
        <span class="scene-hill scene-hill--front"></span>
        <div class="scene-city">
          <span class="tower tower--1"></span>
          <span class="tower tower--2"></span>
          <span class="tower tower--3"></span>
          <span class="tower tower--4"></span>
          <span class="tower tower--5"></span>
        </div>
      </div>

      <button class="punch" type="button" :disabled="disabled" @click="$emit('punch')">
        <span class="punch-label">
          {{
            cooldownRemaining > 0
              ? `${cooldownRemaining}s`
              : loading
                ? '提交中'
                : '打卡'
          }}
        </span>
      </button>

      <div v-if="message" class="msg" :class="`msg--${messageType}`">
        {{ message }}
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import ClockIcon from './ClockIcon.vue'
import MessageIcon from './MessageIcon.vue'
import { getBeijingGreeting } from '../lib/time'

const props = defineProps({
  user: { type: Object, default: null },
  now: { type: [Date, String, Number], default: () => new Date() },
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
const greeting = computed(() => getBeijingGreeting(props.now))
</script>

<style scoped>
.home {
  width: 100%;
  max-width: none;
  padding: 32px 0 120px;
}

.hero {
  padding: 0 18px;
  margin-bottom: 22px;
}

.eyebrow {
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

.hero-copy {
  display: grid;
  justify-items: flex-start;
  gap: 12px;
  text-align: left;
}

.quick-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-start;
}

.quick-btn {
  position: relative;
  width: 28px;
  height: 28px;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  display: inline-grid;
  place-items: center;
  padding: 0;
  color: rgba(24, 59, 77, 0.74);
  transition: transform 0.16s ease, opacity 0.16s ease;
}

.quick-btn:hover {
  transform: translateY(-1px);
  opacity: 0.8;
}

.quick-btn :deep(.icon) {
  width: 20px;
  height: 20px;
}

.dot {
  position: absolute;
  top: 16px;
  right: 18px;
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: #c17d55;
  box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.95);
}

.punch-stage {
  margin-top: 28px;
  min-height: 320px;
  padding: 0 18px;
  position: relative;
  display: grid;
  align-items: center;
  justify-items: center;
  text-align: center;
  overflow: hidden;
}

.scene {
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0.5;
}

.scene-sun {
  position: absolute;
  top: 34px;
  left: 50%;
  width: 76px;
  height: 76px;
  margin-left: -118px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(241, 201, 117, 0.95), rgba(241, 201, 117, 0.22) 60%, transparent 72%);
}

.scene-cloud {
  position: absolute;
  top: 58px;
  height: 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.55);
  filter: blur(0.2px);
}

.scene-cloud::before,
.scene-cloud::after {
  content: '';
  position: absolute;
  bottom: 2px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.55);
}

.scene-cloud--left {
  left: calc(50% - 12px);
  width: 42px;
}

.scene-cloud--left::before {
  left: 4px;
  width: 16px;
  height: 16px;
}

.scene-cloud--left::after {
  right: 5px;
  width: 18px;
  height: 18px;
}

.scene-cloud--right {
  right: calc(50% - 74px);
  width: 48px;
}

.scene-cloud--right::before {
  left: 6px;
  width: 18px;
  height: 18px;
}

.scene-cloud--right::after {
  right: 7px;
  width: 20px;
  height: 20px;
}

.scene-hill {
  position: absolute;
  left: 50%;
  border-radius: 50% 50% 0 0;
  transform: translateX(-50%);
}

.scene-hill--back {
  bottom: 84px;
  width: 300px;
  height: 120px;
  background: linear-gradient(180deg, rgba(180, 220, 194, 0.18), rgba(162, 209, 180, 0.3));
}

.scene-hill--front {
  bottom: 54px;
  width: 360px;
  height: 108px;
  background: linear-gradient(180deg, rgba(146, 205, 170, 0.1), rgba(146, 205, 170, 0.24));
}

.scene-city {
  position: absolute;
  left: 50%;
  bottom: 104px;
  width: 244px;
  height: 110px;
  transform: translateX(-50%);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 10px;
}

.tower {
  width: 28px;
  border-radius: 4px 4px 0 0;
  background: linear-gradient(180deg, rgba(157, 225, 204, 0.5), rgba(127, 204, 182, 0.3));
  position: relative;
}

.tower::before {
  content: '';
  position: absolute;
  inset: 10px 8px 12px;
  border-radius: 2px;
  background: repeating-linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.24) 0 5px,
    transparent 5px 10px
  );
}

.tower--1 {
  height: 58px;
}

.tower--2 {
  height: 90px;
}

.tower--3 {
  height: 106px;
}

.tower--4 {
  height: 82px;
}

.tower--5 {
  height: 66px;
}

.punch {
  width: 176px;
  height: 176px;
  border-radius: 999px;
  border: 1px solid rgba(183, 139, 74, 0.18);
  background: linear-gradient(180deg, rgba(214, 177, 120, 0.98), rgba(191, 144, 74, 0.96));
  color: #fffaf2;
  box-shadow: 0 14px 30px rgba(183, 139, 74, 0.22);
  display: grid;
  place-items: center;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
  position: relative;
  z-index: 1;
}

.punch:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 18px 34px rgba(183, 139, 74, 0.26);
  background: linear-gradient(180deg, rgba(222, 186, 132, 0.98), rgba(197, 151, 82, 0.96));
}

.punch:disabled {
  opacity: 0.64;
  cursor: not-allowed;
  box-shadow: none;
}

.punch-label {
  font-size: 26px;
  letter-spacing: 0.02em;
  font-weight: 800;
}

.msg {
  margin-top: 20px;
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
    margin-bottom: 18px;
  }

  .hero-copy {
    width: 100%;
    text-align: left;
    gap: 10px;
  }

  .title {
    font-size: 30px;
    line-height: 1.06;
  }

  .quick-actions {
    width: auto;
    justify-content: flex-start;
  }

  .quick-btn {
    width: 28px;
    height: 28px;
  }

  .punch {
    width: 156px;
    height: 156px;
  }

  .scene {
    opacity: 0.42;
  }

  .scene-sun {
    top: 42px;
    width: 62px;
    height: 62px;
    margin-left: -94px;
  }

  .scene-city {
    width: 208px;
    gap: 8px;
  }

  .tower {
    width: 24px;
  }

  .scene-hill--back {
    width: 248px;
  }

  .scene-hill--front {
    width: 304px;
  }
}
</style>
