<template>
  <section class="page">
    <header class="hero">
      <div>
        <p class="eyebrow">Programs</p>
        <h2 class="title">把活动页做成一个真正可浏览的内容库。</h2>
        <p class="subtitle">每个活动都应该像一个独立栏目，而不是随手堆出来的列表项。</p>
      </div>
    </header>

    <div class="grid">
      <button v-for="(a, idx) in activities" :key="a.id" class="card" type="button" @click="$emit('open', a.id)">
        <div class="cover" :style="thumbStyle(idx)">
          <div class="cover-noise"></div>
          <span class="badge">{{ a.date }}</span>
          <div class="cover-copy">
            <p class="cover-kicker">Featured Track</p>
            <h3>{{ a.title }}</h3>
          </div>
        </div>

        <div class="meta">
          <p class="tagline">{{ a.tagline }}</p>
          <span class="action">查看详情</span>
        </div>
      </button>
    </div>
  </section>
</template>

<script setup>
defineProps({
  activities: { type: Array, default: () => [] }
})

defineEmits(['open'])

function thumbStyle(index) {
  const palettes = [
    ['#183b4d', '#29546c', '#d7b178'],
    ['#29413b', '#49655d', '#e2c58f'],
    ['#62472f', '#8b6543', '#f1d8ac'],
    ['#2f3a57', '#4e5d7f', '#d5c7a1']
  ]
  const [a, b, glow] = palettes[index % palettes.length]
  return {
    background: `linear-gradient(145deg, ${a}, ${b})`,
    boxShadow: `0 24px 60px color-mix(in srgb, ${glow} 22%, transparent)`
  }
}
</script>

<style scoped>
.page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 32px 18px 120px;
}

.hero {
  margin-bottom: 24px;
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
  max-width: 13ch;
  font-size: clamp(32px, 4vw, 54px);
  line-height: 1.02;
  letter-spacing: -0.05em;
  color: #152131;
}

.subtitle {
  margin: 14px 0 0;
  max-width: 560px;
  font-size: 15px;
  line-height: 1.8;
  color: rgba(24, 33, 47, 0.62);
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.card {
  border: 0;
  padding: 0;
  overflow: hidden;
  border-radius: 30px;
  text-align: left;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 24px 64px rgba(20, 29, 41, 0.1);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 30px 80px rgba(20, 29, 41, 0.14);
}

.cover {
  position: relative;
  min-height: 280px;
  padding: 22px;
  display: flex;
  align-items: flex-end;
}

.cover::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, transparent 20%, rgba(7, 13, 22, 0.2) 100%),
    radial-gradient(circle at 22% 18%, rgba(255, 255, 255, 0.18), transparent 22%);
}

.cover-noise {
  position: absolute;
  inset: -20%;
  background:
    repeating-linear-gradient(135deg, rgba(255, 255, 255, 0.04) 0 12px, transparent 12px 28px),
    radial-gradient(circle at 78% 20%, rgba(215, 177, 120, 0.24), transparent 20%);
  transform: rotate(6deg);
}

.badge,
.cover-copy {
  position: relative;
  z-index: 1;
}

.badge {
  position: absolute;
  top: 18px;
  left: 18px;
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: rgba(248, 244, 236, 0.96);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.cover-copy h3 {
  margin: 8px 0 0;
  font-size: 30px;
  line-height: 1;
  letter-spacing: -0.04em;
  color: #f8f4ec;
}

.cover-kicker {
  margin: 0;
  font-size: 12px;
  color: rgba(248, 244, 236, 0.72);
  letter-spacing: 0.2em;
  text-transform: uppercase;
  font-weight: 800;
}

.meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 18px 22px 20px;
}

.tagline {
  margin: 0;
  color: rgba(24, 33, 47, 0.66);
  line-height: 1.7;
  font-size: 14px;
}

.action {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  min-height: 40px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
