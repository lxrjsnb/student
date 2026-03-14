<template>
  <section class="page">
    <header class="head">
      <div>
        <p class="kicker">活动</p>
        <h2 class="title">今天想参加哪一个？</h2>
      </div>
    </header>

    <div class="list">
      <button v-for="(a, idx) in activities" :key="a.id" class="item" type="button" @click="$emit('open', a.id)">
        <div class="cover" :style="thumbStyle(idx)" aria-hidden="true">
          <div class="coverOverlay" aria-hidden="true"></div>
          <span class="chip">{{ a.date }}</span>
        </div>
        <div class="meta">
          <p class="name">{{ a.title }}</p>
          <p class="tagline">{{ a.tagline }}</p>
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
    ['#cfefff', '#e7fff6', 'rgba(0, 168, 204, 0.22)'],
    ['#ffe7f1', '#fff6db', 'rgba(254, 214, 227, 0.35)'],
    ['#d7ffe9', '#e8f1ff', 'rgba(34, 197, 94, 0.18)'],
    ['#fff1d6', '#e9f7ff', 'rgba(245, 158, 11, 0.18)']
  ]
  const [a, b, glow] = palettes[index % palettes.length]
  return {
    background: `linear-gradient(135deg, ${a}, ${b})`,
    boxShadow: `0 18px 44px ${glow}`
  }
}
</script>

<style scoped>
.page {
  padding: 18px 16px 92px;
  max-width: 720px;
  margin: 0 auto;
}

.head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.kicker {
  margin: 0;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.6);
}

.title {
  margin: 4px 0 0;
  font-size: 18px;
  font-weight: 900;
  letter-spacing: 0.2px;
  color: rgba(15, 23, 42, 0.9);
}

.list {
  display: grid;
  gap: 12px;
}

.item {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  align-items: stretch;
  padding: 12px 12px 14px;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.66);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.14);
  text-align: left;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.item:hover {
  transform: translateY(-1px);
}

.cover {
  position: relative;
  width: 100%;
  height: 160px;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.coverOverlay {
  position: absolute;
  inset: -40%;
  background:
    radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.6), transparent 42%),
    radial-gradient(circle at 80% 30%, rgba(255, 255, 255, 0.35), transparent 46%),
    repeating-linear-gradient(45deg, rgba(255, 255, 255, 0.2) 0 10px, transparent 10px 26px);
  filter: blur(16px);
  transform: rotate(8deg);
}

.name {
  margin: 0;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.88);
  letter-spacing: 0.2px;
}

.tagline {
  margin: 6px 0 0;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.62);
}

.chip {
  position: absolute;
  top: 10px;
  left: 10px;
  font-size: 12px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.72);
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}
</style>
