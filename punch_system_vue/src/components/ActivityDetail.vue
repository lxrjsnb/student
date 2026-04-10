<template>
  <section v-if="activity" class="page">
    <header class="head">
      <button class="back" type="button" @click="$emit('back')">返回列表</button>
      <span class="section-tag">Program Detail</span>
    </header>

    <div class="hero" :style="heroStyle">
      <div class="hero-overlay"></div>
      <div class="hero-copy">
        <span class="date">{{ activity.date }}</span>
        <h2 class="title">{{ activity.title }}</h2>
        <p class="tagline">{{ activity.tagline }}</p>
      </div>
    </div>

    <div class="content-shell">
      <article class="card">
        <p class="card-kicker">How It Works</p>
        <div class="steps">
          <div v-for="(p, idx) in activity.content" :key="idx" class="step">
            <span class="step-index">{{ String(idx + 1).padStart(2, '0') }}</span>
            <p>{{ p }}</p>
          </div>
        </div>
      </article>
    </div>
  </section>

  <section v-else class="page">
    <header class="head">
      <button class="back" type="button" @click="$emit('back')">返回列表</button>
    </header>
    <div class="empty">活动不存在或已下线</div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  activity: { type: Object, default: null }
})

defineEmits(['back'])

const heroStyle = computed(() => {
  const id = props.activity?.id || ''
  const hue = Math.abs(hashCode(id)) % 360
  return {
    background: `linear-gradient(145deg, hsla(${hue}, 34%, 24%, 1), hsla(${(hue + 24) % 360}, 28%, 36%, 1))`
  }
})

function hashCode(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) hash = (hash << 5) - hash + str.charCodeAt(i)
  return hash
}
</script>

<style scoped>
.page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 32px 18px 120px;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.back,
.section-tag {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding: 0 16px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.back {
  border: 0;
  background: rgba(255, 255, 255, 0.74);
  color: #183b4d;
  box-shadow: 0 14px 30px rgba(20, 29, 41, 0.08);
}

.section-tag {
  background: rgba(24, 59, 77, 0.08);
  color: rgba(24, 59, 77, 0.72);
}

.hero {
  position: relative;
  min-height: 420px;
  border-radius: 34px;
  overflow: hidden;
  display: flex;
  align-items: flex-end;
  padding: 28px;
  box-shadow: 0 28px 90px rgba(20, 29, 41, 0.18);
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(7, 13, 22, 0.4)),
    radial-gradient(circle at 78% 18%, rgba(215, 177, 120, 0.24), transparent 20%),
    repeating-linear-gradient(135deg, rgba(255, 255, 255, 0.04) 0 12px, transparent 12px 28px);
}

.hero-copy {
  position: relative;
  z-index: 1;
  max-width: 640px;
}

.date {
  display: inline-flex;
  min-height: 34px;
  padding: 0 12px;
  align-items: center;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: rgba(248, 244, 236, 0.88);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.title {
  margin: 16px 0 0;
  font-size: clamp(42px, 5vw, 74px);
  line-height: 0.94;
  letter-spacing: -0.06em;
  color: #f8f4ec;
}

.tagline {
  margin: 16px 0 0;
  max-width: 520px;
  font-size: 16px;
  line-height: 1.8;
  color: rgba(248, 244, 236, 0.72);
}

.content-shell {
  margin-top: 18px;
  border-radius: 30px;
  padding: 18px;
  background: rgba(255, 255, 255, 0.28);
  border: 1px solid rgba(24, 33, 47, 0.06);
}

.card {
  border-radius: 28px;
  padding: 28px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 24px 64px rgba(20, 29, 41, 0.08);
}

.card-kicker {
  margin: 0 0 16px;
  color: rgba(24, 59, 77, 0.6);
  font-size: 12px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  font-weight: 800;
}

.steps {
  display: grid;
  gap: 14px;
}

.step {
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: 16px;
  align-items: start;
  padding: 18px;
  border-radius: 22px;
  background: rgba(248, 242, 231, 0.68);
  border: 1px solid rgba(24, 33, 47, 0.06);
}

.step-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  border-radius: 14px;
  background: #183b4d;
  color: #f8f4ec;
  font-weight: 800;
  letter-spacing: 0.1em;
}

.step p {
  margin: 0;
  font-size: 15px;
  line-height: 1.8;
  color: rgba(24, 33, 47, 0.76);
}

.empty {
  padding: 40px 0;
  text-align: center;
  color: rgba(24, 33, 47, 0.58);
}

@media (max-width: 760px) {
  .head {
    flex-wrap: wrap;
  }

  .hero {
    min-height: 320px;
    padding: 20px;
  }

  .step {
    grid-template-columns: 1fr;
  }
}
</style>
