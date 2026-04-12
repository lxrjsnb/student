<template>
  <section v-if="activity" class="page">
    <header class="head">
      <button class="back" type="button" aria-label="返回活动库" title="返回活动库" @click="$emit('back')">‹</button>
    </header>

    <section class="hero" :style="heroStyle">
      <div class="heroShade"></div>
      <div class="heroCopy">
        <div class="metaRow">
          <span class="pill">{{ activity.category }}</span>
          <span class="pill">{{ activity.frequency }}</span>
          <span class="pill">{{ activity.duration }}</span>
        </div>
        <h2 class="title">{{ activity.title }}</h2>
        <p class="tagline">{{ activity.tagline }}</p>
        <p class="summary">{{ activity.description }}</p>
      </div>
    </section>

    <section class="overview">
      <div class="infoCard">
        <span class="label">难度</span>
        <strong class="value">{{ activity.difficulty }}</strong>
      </div>
      <div class="infoCard">
        <span class="label">适合场景</span>
        <strong class="value">{{ activity.scene }}</strong>
      </div>
      <div class="infoCard">
        <span class="label">执行频率</span>
        <strong class="value">{{ activity.frequency }}</strong>
      </div>
    </section>

    <section class="contentGrid">
      <article class="sectionCard">
        <p class="sectionKicker">How To Start</p>
        <h3 class="sectionTitle">活动步骤</h3>
        <div class="steps">
          <div v-for="(step, idx) in activity.steps" :key="idx" class="step">
            <span class="stepIndex">{{ String(idx + 1).padStart(2, '0') }}</span>
            <p>{{ step }}</p>
          </div>
        </div>
      </article>

      <aside class="sideCol">
        <article class="sectionCard">
          <p class="sectionKicker">Highlights</p>
          <h3 class="sectionTitle">你会得到什么</h3>
          <div class="tagList">
            <span v-for="item in activity.highlights" :key="item" class="tag">{{ item }}</span>
          </div>
        </article>

        <article class="sectionCard">
          <p class="sectionKicker">Tiny Tips</p>
          <h3 class="sectionTitle">执行建议</h3>
          <ul class="tips">
            <li v-for="tip in activity.tips" :key="tip">{{ tip }}</li>
          </ul>
        </article>
      </aside>
    </section>
  </section>

  <section v-else class="page">
    <header class="head">
      <button class="back" type="button" aria-label="返回活动库" title="返回活动库" @click="$emit('back')">‹</button>
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
  if (props.activity?.coverImage) {
    return {
      backgroundImage: `linear-gradient(180deg, rgba(7, 13, 22, 0.04), rgba(7, 13, 22, 0.22)), url(${props.activity.coverImage})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  const palettes = {
    '运动激活': ['#6d8b74', '#9dc4a8'],
    '身体舒展': ['#688580', '#a5c1bc'],
    '学习成长': ['#657898', '#aeb8d3'],
    '生活习惯': ['#a87f48', '#d7b178'],
    '恢复休息': ['#81906a', '#becd9f'],
    '空间整理': ['#8d7764', '#ccb29b'],
    '情绪感知': ['#8e7080', '#c9adba']
  }
  const [a, b] = palettes[props.activity?.category] || ['#183b4d', '#5f7b89']
  return {
    background: `linear-gradient(145deg, ${a}, ${b})`
  }
})
</script>

<style scoped>
.page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 32px 18px 120px;
}

.head {
  margin-bottom: 18px;
}

.back {
  width: 32px;
  height: 32px;
  display: inline-grid;
  place-items: center;
  padding: 0;
  border-radius: 999px;
  border: 0;
  background: transparent;
  color: rgba(24, 59, 77, 0.78);
  font-size: 28px;
  line-height: 1;
}

.hero {
  position: relative;
  min-height: 360px;
  border-radius: 34px;
  overflow: hidden;
  padding: 26px;
  display: flex;
  align-items: flex-end;
  box-shadow: 0 26px 72px rgba(20, 29, 41, 0.16);
}

.heroShade {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(7, 13, 22, 0.28)),
    radial-gradient(circle at 80% 22%, rgba(255, 255, 255, 0.18), transparent 22%),
    repeating-linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0 12px, transparent 12px 28px);
}

.heroCopy {
  position: relative;
  z-index: 1;
  max-width: 720px;
}

.metaRow {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pill {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.14);
  color: rgba(248, 244, 236, 0.92);
  font-size: 12px;
  font-weight: 800;
}

.title {
  margin: 14px 0 0;
  font-size: clamp(40px, 5vw, 72px);
  line-height: 0.94;
  letter-spacing: -0.06em;
  color: #f8f4ec;
}

.tagline {
  margin: 14px 0 0;
  font-size: 18px;
  line-height: 1.7;
  color: rgba(248, 244, 236, 0.8);
}

.summary {
  margin: 12px 0 0;
  max-width: 56ch;
  font-size: 15px;
  line-height: 1.85;
  color: rgba(248, 244, 236, 0.74);
}

.overview {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 18px;
}

.infoCard,
.sectionCard {
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(24, 33, 47, 0.06);
  box-shadow: 0 20px 48px rgba(20, 29, 41, 0.06);
}

.infoCard {
  padding: 16px 18px;
}

.label {
  display: block;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(24, 59, 77, 0.52);
}

.value {
  display: block;
  margin-top: 10px;
  font-size: 22px;
  line-height: 1.15;
  color: #152131;
  letter-spacing: -0.03em;
}

.contentGrid {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(320px, 0.7fr);
  gap: 18px;
  margin-top: 18px;
}

.sectionCard {
  padding: 24px;
}

.sectionKicker {
  margin: 0 0 10px;
  color: rgba(24, 59, 77, 0.56);
  font-size: 12px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  font-weight: 800;
}

.sectionTitle {
  margin: 0;
  font-size: 24px;
  line-height: 1.1;
  letter-spacing: -0.04em;
  color: #152131;
}

.steps {
  display: grid;
  gap: 14px;
  margin-top: 18px;
}

.step {
  display: grid;
  grid-template-columns: 60px 1fr;
  gap: 16px;
  align-items: start;
  padding: 18px;
  border-radius: 22px;
  background: rgba(248, 242, 231, 0.68);
  border: 1px solid rgba(24, 33, 47, 0.05);
}

.stepIndex {
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

.sideCol {
  display: grid;
  gap: 18px;
}

.tagList {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.tag {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(215, 177, 120, 0.14);
  color: #805c20;
  font-size: 13px;
  font-weight: 700;
}

.tips {
  margin: 18px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}

.tips li {
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(248, 242, 231, 0.58);
  border: 1px solid rgba(24, 33, 47, 0.05);
  color: rgba(24, 33, 47, 0.74);
  line-height: 1.75;
}

.empty {
  padding: 40px 0;
  text-align: center;
  color: rgba(24, 33, 47, 0.58);
}

@media (max-width: 900px) {
  .overview,
  .contentGrid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .hero {
    min-height: 300px;
    padding: 20px;
  }

  .step {
    grid-template-columns: 1fr;
  }
}
</style>
