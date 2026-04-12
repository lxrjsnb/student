<template>
  <section class="page">
    <header class="hero">
      <p class="eyebrow">Daily Library</p>
      <h2 class="title">日常活动</h2>
    </header>

    <section class="toolbar">
      <label class="search">
        <input v-model.trim="keyword" class="searchInput" type="search" placeholder="搜索活动名称、场景或关键词" />
      </label>
    </section>

    <div v-if="filteredActivities.length" class="grid">
      <button v-for="(activity, idx) in filteredActivities" :key="activity.id" class="card" type="button" @click="$emit('open', activity.id)">
        <div class="cover" :style="thumbStyle(activity, idx)">
          <img v-if="activity.coverImage" class="coverImage" :src="activity.coverImage" alt="" />
          <span class="coverTag">{{ activity.category }}</span>
          <div class="coverCopy">
            <p class="coverMeta">{{ activity.frequency }} · {{ activity.duration }}</p>
            <h3>{{ activity.title }}</h3>
            <p>{{ activity.tagline }}</p>
          </div>
        </div>

        <div class="meta">
          <p class="summaryText">{{ activity.summary }}</p>

          <div class="facts">
            <span class="fact">{{ activity.difficulty }}</span>
            <span class="fact">{{ activity.scene }}</span>
          </div>

          <div class="highlights">
            <span v-for="highlight in activity.highlights.slice(0, 2)" :key="highlight" class="highlight">{{ highlight }}</span>
          </div>

          <span class="action">查看内容</span>
        </div>
      </button>
    </div>

    <div v-else class="empty">
      <p class="emptyTitle">没有找到匹配内容</p>
      <p class="emptyText">试着换一个关键词，或者切回“全部”分类。</p>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  activities: { type: Array, default: () => [] }
})

defineEmits(['open'])

const keyword = ref('')
const filteredActivities = computed(() => {
  const q = keyword.value.toLowerCase()
  return (props.activities || []).filter((item) => {
    if (!q) return true
    return [item.title, item.tagline, item.summary, item.scene, item.category, ...(item.highlights || [])]
      .filter(Boolean)
      .some((text) => String(text).toLowerCase().includes(q))
  })
})

function thumbStyle(activity, index) {
  const palettes = {
    '运动激活': ['#6d8b74', '#9dc4a8', '#d7e8d7'],
    '身体舒展': ['#6f9089', '#a9cbc3', '#e6f1ef'],
    '学习成长': ['#7c8ca8', '#b4c0d8', '#eceff7'],
    '生活习惯': ['#b78b4a', '#d7b178', '#f2e1be'],
    '恢复休息': ['#8e9c74', '#c5d3aa', '#edf1e0'],
    '空间整理': ['#9b8571', '#d2b9a2', '#f1e7dc'],
    '情绪感知': ['#9f7f8f', '#d3b5c2', '#f3e8ee']
  }
  const fallback = [
    ['#183b4d', '#4f7081', '#d7e6ea'],
    ['#6d8b74', '#9bb7a2', '#e5efe8'],
    ['#b78b4a', '#d9bb87', '#f3e5c9']
  ]
  const [start, end, glow] = palettes[activity.category] || fallback[index % fallback.length]
  return {
    background: `linear-gradient(145deg, ${start}, ${end})`,
    boxShadow: `inset 0 1px 0 rgba(255,255,255,0.18), 0 24px 48px color-mix(in srgb, ${glow} 36%, transparent)`
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
  font-size: clamp(34px, 4vw, 56px);
  line-height: 0.98;
  letter-spacing: -0.05em;
  color: #152131;
}

.toolbar {
  display: grid;
  gap: 16px;
  margin-bottom: 16px;
}

.search {
  display: grid;
  gap: 8px;
}

.searchInput {
  width: 100%;
  min-height: 52px;
  border-radius: 18px;
  border: 1px solid rgba(24, 33, 47, 0.08);
  background: rgba(255, 255, 255, 0.76);
  padding: 0 16px;
  font-size: 15px;
  color: #18212f;
  outline: none;
  box-shadow: 0 14px 34px rgba(20, 29, 41, 0.05);
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
  border-radius: 28px;
  text-align: left;
  background: rgba(255, 255, 255, 0.74);
  box-shadow: 0 22px 54px rgba(20, 29, 41, 0.08);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 28px 68px rgba(20, 29, 41, 0.12);
}

.cover {
  min-height: 218px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
}

.coverImage {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(7, 13, 22, 0.18)),
    radial-gradient(circle at 78% 18%, rgba(255, 255, 255, 0.18), transparent 24%);
}

.coverTag,
.coverCopy {
  position: relative;
  z-index: 1;
}

.coverTag {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  width: fit-content;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: rgba(248, 244, 236, 0.96);
  font-size: 12px;
  font-weight: 800;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.coverMeta {
  margin: 0;
  color: rgba(248, 244, 236, 0.8);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.coverCopy h3 {
  margin: 10px 0 0;
  font-size: 30px;
  line-height: 1.02;
  letter-spacing: -0.04em;
  color: #f8f4ec;
}

.coverCopy p:last-child {
  margin: 10px 0 0;
  max-width: 28ch;
  color: rgba(248, 244, 236, 0.76);
  line-height: 1.7;
  font-size: 14px;
}

.meta {
  padding: 18px 18px 20px;
}

.summaryText {
  margin: 0;
  color: rgba(24, 33, 47, 0.72);
  line-height: 1.8;
  font-size: 14px;
}

.facts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.fact,
.highlight {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.fact {
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
}

.highlights {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.highlight {
  background: rgba(215, 177, 120, 0.14);
  color: #805c20;
}

.action {
  display: inline-flex;
  align-items: center;
  min-height: 40px;
  margin-top: 16px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.empty {
  padding: 48px 18px;
  text-align: center;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(24, 33, 47, 0.06);
}

.emptyTitle {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  color: #152131;
}

.emptyText {
  margin: 10px 0 0;
  color: rgba(24, 33, 47, 0.62);
  line-height: 1.7;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
