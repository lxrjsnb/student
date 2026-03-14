<template>
  <div v-if="open" class="wrap" role="dialog" aria-modal="true" @click.self="$emit('close')">
    <div class="panel">
      <div class="pattern" aria-hidden="true"></div>

      <div class="content">
        <div class="badge" aria-hidden="true">✓</div>
        <h3 class="title">已提交管理员</h3>
        <p class="sub">待审批通过后计入历史记录</p>

        <div class="quote">
          <p class="q">“{{ quote }}”</p>
          <p v-if="from" class="from">— {{ from }}</p>
        </div>

        <button class="ok" type="button" @click="$emit('close')">知道了</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  open: { type: Boolean, default: false },
  quote: { type: String, default: '' },
  from: { type: String, default: '' }
})

defineEmits(['close'])
</script>

<style scoped>
.wrap {
  position: fixed;
  inset: 0;
  background: rgba(2, 6, 23, 0.35);
  display: grid;
  place-items: center;
  padding: 18px;
  z-index: 50;
}

.panel {
  width: min(520px, 100%);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 26px 70px rgba(15, 23, 42, 0.28);
  overflow: hidden;
  position: relative;
}

.pattern {
  position: absolute;
  inset: -60%;
  background:
    radial-gradient(circle at 22% 24%, rgba(255, 241, 138, 0.65), transparent 38%),
    radial-gradient(circle at 78% 28%, rgba(0, 168, 204, 0.22), transparent 44%),
    radial-gradient(circle at 42% 76%, rgba(254, 214, 227, 0.42), transparent 52%),
    conic-gradient(
      from 10deg at 52% 52%,
      rgba(255, 255, 255, 0.35),
      rgba(255, 255, 255, 0.12),
      rgba(255, 255, 255, 0.28),
      rgba(255, 255, 255, 0.1),
      rgba(255, 255, 255, 0.35)
    ),
    repeating-linear-gradient(0deg, rgba(255, 255, 255, 0.18) 0 10px, transparent 10px 26px),
    repeating-linear-gradient(90deg, rgba(255, 255, 255, 0.12) 0 10px, transparent 10px 26px);
  filter: blur(14px);
  transform: rotate(6deg);
  opacity: 0.92;
}

.content {
  position: relative;
  padding: 18px 18px 16px;
  text-align: center;
}

.badge {
  width: 46px;
  height: 46px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  margin: 0 auto 10px;
  background: rgba(34, 197, 94, 0.16);
  color: #15803d;
  border: 1px solid rgba(34, 197, 94, 0.22);
  font-weight: 900;
}

.title {
  margin: 0;
  font-size: 18px;
  font-weight: 1000;
  letter-spacing: 0.2px;
  color: rgba(15, 23, 42, 0.88);
}

.sub {
  margin: 8px 0 0;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.62);
}

.quote {
  margin: 14px 0 14px;
  padding: 12px 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.66);
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.q {
  margin: 0;
  font-size: 14px;
  font-weight: 800;
  color: rgba(0, 95, 120, 1);
  line-height: 1.55;
}

.from {
  margin: 8px 0 0;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.6);
}

.ok {
  width: 100%;
  border: 0;
  border-radius: 16px;
  padding: 12px 14px;
  background: linear-gradient(135deg, rgba(0, 168, 204, 0.95), rgba(0, 139, 168, 0.95));
  color: white;
  font-weight: 900;
  font-size: 14px;
  box-shadow: 0 18px 34px rgba(0, 168, 204, 0.24);
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.ok:hover {
  transform: translateY(-1px);
  box-shadow: 0 22px 40px rgba(0, 168, 204, 0.3);
}
</style>
