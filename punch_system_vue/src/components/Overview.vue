<template>
  <div class="overview">
    <div class="overview__header">
      <h2 class="overview__title">概览</h2>
      <p class="overview__subtitle">查看校园信息与图片</p>
    </div>

    <div class="overview__content">
      <div class="info-section">
        <h3 class="section-title">📢 校园公告</h3>
        <div class="info-cards">
          <div class="info-card">
            <div class="info-card__icon">🎓</div>
            <div class="info-card__content">
              <h4 class="info-card__title">开学通知</h4>
              <p class="info-card__text">2024年春季学期将于3月1日正式开学，请各位同学提前做好准备。</p>
              <p class="info-card__date">2024-02-20</p>
            </div>
          </div>
          <div class="info-card">
            <div class="info-card__icon">📚</div>
            <div class="info-card__content">
              <h4 class="info-card__title">图书馆开放时间</h4>
              <p class="info-card__text">图书馆开放时间为周一至周五 8:00-22:00，周末 9:00-21:00。</p>
              <p class="info-card__date">2024-02-18</p>
            </div>
          </div>
          <div class="info-card">
            <div class="info-card__icon">🏃</div>
            <div class="info-card__content">
              <h4 class="info-card__title">体育设施开放</h4>
              <p class="info-card__text">体育馆、游泳池等体育设施已全面开放，欢迎同学们前来锻炼。</p>
              <p class="info-card__date">2024-02-15</p>
            </div>
          </div>
        </div>
      </div>

      <div class="info-section">
        <h3 class="section-title">🖼️ 校园风光</h3>
        <div class="gallery">
          <div class="gallery-item" v-for="(image, index) in images" :key="index" @click="openImage(index)">
            <div class="gallery-item__image" :style="{ backgroundImage: `url(${image.url})` }"></div>
            <div class="gallery-item__overlay">
              <span class="gallery-item__title">{{ image.title }}</span>
              <span class="gallery-item__icon">🔍</span>
            </div>
          </div>
        </div>
      </div>

      <div class="info-section">
        <h3 class="section-title">📊 个人统计</h3>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-item__icon">⭐</div>
            <div class="stat-item__content">
              <p class="stat-item__value">{{ user.score || 0 }}</p>
              <p class="stat-item__label">当前分数</p>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-item__icon">📋</div>
            <div class="stat-item__content">
              <p class="stat-item__value">{{ records.length }}</p>
              <p class="stat-item__label">签到次数</p>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-item__icon">📅</div>
            <div class="stat-item__content">
              <p class="stat-item__value">{{ todayCount }}</p>
              <p class="stat-item__label">今日签到</p>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-item__icon">🎯</div>
            <div class="stat-item__content">
              <p class="stat-item__value">{{ streakDays }}</p>
              <p class="stat-item__label">连续签到</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showModal" class="modal" @click="closeModal">
      <div class="modal__content" @click.stop>
        <button class="modal__close" @click="closeModal">✕</button>
        <div class="modal__image" :style="{ backgroundImage: `url(${currentImage?.url})` }"></div>
        <div class="modal__info">
          <h3 class="modal__title">{{ currentImage?.title }}</h3>
          <p class="modal__description">{{ currentImage?.description }}</p>
        </div>
        <div class="modal__nav">
          <button class="modal__nav-btn" @click="prevImage" :disabled="currentIndex === 0">❮ 上一张</button>
          <span class="modal__counter">{{ currentIndex + 1 }} / {{ images.length }}</span>
          <button class="modal__nav-btn" @click="nextImage" :disabled="currentIndex === images.length - 1">下一张 ❯</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  user: {
    type: Object,
    required: true
  },
  records: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['goHome'])

const showModal = ref(false)
const currentIndex = ref(0)

const images = ref([
  {
    url: 'https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=800&q=80',
    title: '校园图书馆',
    description: '现代化的图书馆，藏书丰富，环境优雅，是学习和阅读的理想场所。'
  },
  {
    url: 'https://images.unsplash.com/photo-1562774053-701939374585?w=800&q=80',
    title: '教学楼',
    description: '宽敞明亮的教学楼，配备先进的教学设备，为师生提供优质的教学环境。'
  },
  {
    url: 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&q=80',
    title: '运动场',
    description: '标准化的运动场地，包括跑道、篮球场、足球场等，满足各种运动需求。'
  },
  {
    url: 'https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=800&q=80',
    title: '学生宿舍',
    description: '舒适的学生宿舍，设施齐全，为学生提供温馨的居住环境。'
  },
  {
    url: 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&q=80',
    title: '校园湖景',
    description: '美丽的校园湖泊，四季景色各异，是师生休闲放松的好去处。'
  },
  {
    url: 'https://images.unsplash.com/photo-1564981797816-1043664bf78d?w=800&q=80',
    title: '实验楼',
    description: '设备先进的实验楼，配备各种专业实验室，支持科研和教学活动。'
  }
])

const currentImage = computed(() => images.value[currentIndex.value])

const todayCount = computed(() => {
  const today = new Date().toDateString()
  return props.records.filter(record => new Date(record.created_at).toDateString() === today).length
})

const streakDays = computed(() => {
  if (props.records.length === 0) return 0
  
  const sortedRecords = [...props.records].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  let streak = 0
  let currentDate = today
  
  for (const record of sortedRecords) {
    const recordDate = new Date(record.created_at)
    recordDate.setHours(0, 0, 0, 0)
    
    const diffDays = Math.floor((currentDate - recordDate) / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) {
      streak++
      currentDate = new Date(currentDate)
      currentDate.setDate(currentDate.getDate() - 1)
    } else if (diffDays === 1) {
      streak++
      currentDate = new Date(currentDate)
      currentDate.setDate(currentDate.getDate() - 1)
    } else {
      break
    }
  }
  
  return streak
})

function openImage(index) {
  currentIndex.value = index
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

function nextImage() {
  if (currentIndex.value < images.value.length - 1) {
    currentIndex.value++
  }
}

function prevImage() {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}
</script>

<style scoped>
.overview {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.overview__header {
  margin-bottom: 32px;
}

.overview__title {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px;
}

.overview__subtitle {
  font-size: 16px;
  color: #64748b;
  margin: 0;
}

.overview__content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.info-section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.info-card {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.info-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
}

.info-card__icon {
  font-size: 32px;
  flex-shrink: 0;
}

.info-card__content {
  flex: 1;
}

.info-card__title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px;
}

.info-card__text {
  font-size: 14px;
  opacity: 0.9;
  margin: 0 0 12px;
  line-height: 1.5;
}

.info-card__date {
  font-size: 12px;
  opacity: 0.7;
  margin: 0;
}

.gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.gallery-item {
  position: relative;
  aspect-ratio: 16/10;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.gallery-item:hover {
  transform: scale(1.05);
}

.gallery-item__image {
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  transition: transform 0.5s ease;
}

.gallery-item:hover .gallery-item__image {
  transform: scale(1.1);
}

.gallery-item__overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.8) 0%, transparent 60%);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 16px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.gallery-item:hover .gallery-item__overlay {
  opacity: 1;
}

.gallery-item__title {
  color: white;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.gallery-item__icon {
  color: white;
  font-size: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border-radius: 12px;
  color: white;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(240, 147, 251, 0.4);
}

.stat-item__icon {
  font-size: 36px;
  flex-shrink: 0;
}

.stat-item__value {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 4px;
}

.stat-item__label {
  font-size: 14px;
  opacity: 0.9;
  margin: 0;
}

.modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal__content {
  background: white;
  border-radius: 16px;
  max-width: 900px;
  width: 100%;
  overflow: hidden;
  position: relative;
}

.modal__close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 40px;
  height: 40px;
  border: none;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
  z-index: 10;
  transition: background 0.3s ease;
}

.modal__close:hover {
  background: white;
}

.modal__image {
  width: 100%;
  aspect-ratio: 16/10;
  background-size: cover;
  background-position: center;
}

.modal__info {
  padding: 24px;
}

.modal__title {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 12px;
}

.modal__description {
  font-size: 16px;
  color: #64748b;
  margin: 0;
  line-height: 1.6;
}

.modal__nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.modal__nav-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.modal__nav-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.modal__nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal__counter {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

@media (max-width: 768px) {
  .overview {
    padding: 16px;
  }

  .overview__title {
    font-size: 24px;
  }

  .info-cards,
  .gallery,
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .modal__content {
    max-height: 90vh;
    overflow-y: auto;
  }

  .modal__nav {
    flex-direction: column;
    gap: 12px;
  }
}
</style>