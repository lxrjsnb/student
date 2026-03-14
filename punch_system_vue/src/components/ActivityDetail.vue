<template>
  <section v-if="activity" class="page">
    <header class="head">
      <button class="back" type="button" @click="$emit('back')">‹ 返回</button>
    </header>

    <div class="hero" :style="heroStyle" aria-hidden="true"></div>

    <div class="card">
      <p class="date">{{ activity.date }}</p>
      <h2 class="title">{{ activity.title }}</h2>
      <p class="tagline">{{ activity.tagline }}</p>

      <div class="content">
        <p v-for="(p, idx) in activity.content" :key="idx" class="p">
          {{ p }}
        </p>
      </div>
    </div>
  </section>

  <section v-else class="page">
    <header class="head">
      <button class="back" type="button" @click="$emit('back')">‹ 返回</button>
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
    background: `linear-gradient(135deg, hsla(${hue}, 92%, 84%, 1), hsla(${(hue + 40) % 360}, 92%, 90%, 1))`
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
  padding: 18px 16px 92px;
  max-width: 720px;
  margin: 0 auto;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.back {
  border: 0;
  background: rgba(255, 255, 255, 0.66);
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 14px;
  padding: 10px 12px;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.12);
  font-weight: 800;
  color: rgba(15, 23, 42, 0.8);
}

.hero {
  width: 100%;
  height: 180px;
  border-radius: 20px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.14);
}

.card {
  margin-top: 12px;
  border-radius: 20px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.66);
  border: 1px solid rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.14);
}

.date {
  margin: 0;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.6);
}

.title {
  margin: 6px 0 0;
  font-size: 18px;
  font-weight: 1000;
  color: rgba(15, 23, 42, 0.9);
  letter-spacing: 0.2px;
}

.tagline {
  margin: 8px 0 0;
  font-size: 13px;
  color: rgba(15, 23, 42, 0.62);
}

.content {
  margin-top: 12px;
  display: grid;
  gap: 10px;
}

.p {
  margin: 0;
  font-size: 14px;
  color: rgba(15, 23, 42, 0.78);
  line-height: 1.7;
}

.empty {
  padding: 28px 0;
  text-align: center;
  color: rgba(15, 23, 42, 0.6);
  font-size: 13px;
}
</style>

