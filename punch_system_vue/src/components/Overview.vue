<template>
  <div class="overview">
    <div class="overview__header">
      <div class="header-content">
        <div>
          <h2 class="overview__title">概览</h2>
          <p class="overview__subtitle">查看校园信息与图片</p>
        </div>
        <button v-if="isAdmin" class="edit-btn" @click="toggleEditMode">
          {{ isEditMode ? '✓ 保存修改' : '✏️ 编辑内容' }}
        </button>
      </div>
    </div>

    <div class="overview__content">
      <div class="info-section">
        <div class="section-header">
          <h3 class="section-title">📢 校园公告</h3>
          <button v-if="isEditMode" class="add-btn" @click="addAnnouncement">+ 添加公告</button>
        </div>
        <div class="info-cards">
          <div 
            v-for="(announcement, index) in announcements" 
            :key="index" 
            class="info-card"
            :class="{ 'info-card--editable': isEditMode }"
          >
            <div v-if="!isEditMode" class="info-card__icon">{{ announcement.icon }}</div>
            <div v-else class="icon-selector">
              <select v-model="announcement.icon" class="icon-select">
                <option value="🎓">🎓</option>
                <option value="📚">📚</option>
                <option value="🏃">🏃</option>
                <option value="🎉">🎉</option>
                <option value="📢">📢</option>
                <option value="⚠️">⚠️</option>
                <option value="💡">💡</option>
                <option value="🎯">🎯</option>
              </select>
            </div>
            <div class="info-card__content">
              <input 
                v-if="isEditMode" 
                v-model="announcement.title" 
                class="edit-input edit-input--title"
                placeholder="公告标题"
              />
              <h4 v-else class="info-card__title">{{ announcement.title }}</h4>
              <textarea 
                v-if="isEditMode" 
                v-model="announcement.content" 
                class="edit-input edit-input--text"
                placeholder="公告内容"
                rows="2"
              ></textarea>
              <p v-else class="info-card__text">{{ announcement.content }}</p>
              <input 
                v-if="isEditMode" 
                v-model="announcement.date" 
                type="date" 
                class="edit-input edit-input--date"
              />
              <p v-else class="info-card__date">{{ announcement.date }}</p>
              <button v-if="isEditMode" class="delete-btn" @click="removeAnnouncement(index)">删除</button>
            </div>
          </div>
        </div>
      </div>

      <div class="info-section">
        <div class="section-header">
          <h3 class="section-title">🖼️ 校园风光</h3>
          <button v-if="isEditMode" class="add-btn" @click="addImage">+ 添加图片</button>
        </div>
        <div class="gallery">
          <div 
            v-for="(image, index) in images" 
            :key="index" 
            class="gallery-item"
            :class="{ 'gallery-item--editable': isEditMode }"
            @click="!isEditMode && openImage(index)"
          >
            <div class="gallery-item__image" :style="{ backgroundImage: `url(${image.url})` }"></div>
            <div v-if="isEditMode" class="edit-overlay">
              <input 
                v-model="image.url" 
                class="edit-input edit-input--url" 
                placeholder="图片URL"
              />
              <input 
                v-model="image.title" 
                class="edit-input edit-input--img-title" 
                placeholder="图片标题"
              />
              <textarea 
                v-model="image.description" 
                class="edit-input edit-input--desc" 
                placeholder="图片描述"
                rows="2"
              ></textarea>
              <button class="delete-btn delete-btn--img" @click="removeImage(index)">删除</button>
            </div>
            <div v-else class="gallery-item__overlay">
              <span class="gallery-item__title">{{ image.title }}</span>
              <span class="gallery-item__icon">🔍</span>
            </div>
          </div>
        </div>
      </div>

      <div class="info-section">
        <div class="section-header">
          <h3 class="section-title">📊 个人统计</h3>
        </div>
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

      <div class="info-section">
        <div class="section-header">
          <h3 class="section-title">📰 最新动态</h3>
          <button v-if="isEditMode" class="add-btn" @click="addNews">+ 添加动态</button>
        </div>
        <div class="news-list">
          <div 
            v-for="(news, index) in news" 
            :key="index" 
            class="news-item"
            :class="{ 'news-item--editable': isEditMode }"
          >
            <div class="news-item__icon">{{ news.icon }}</div>
            <div class="news-item__content">
              <input 
                v-if="isEditMode" 
                v-model="news.title" 
                class="edit-input edit-input--news-title"
                placeholder="动态标题"
              />
              <h4 v-else class="news-item__title">{{ news.title }}</h4>
              <textarea 
                v-if="isEditMode" 
                v-model="news.content" 
                class="edit-input edit-input--news-content"
                placeholder="动态内容"
                rows="2"
              ></textarea>
              <p v-else class="news-item__content-text">{{ news.content }}</p>
              <input 
                v-if="isEditMode" 
                v-model="news.time" 
                class="edit-input edit-input--time"
                placeholder="时间"
              />
              <p v-else class="news-item__time">{{ news.time }}</p>
              <button v-if="isEditMode" class="delete-btn delete-btn--news" @click="removeNews(index)">删除</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showModal && !isEditMode" class="modal" @click="closeModal">
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
  },
  isAdmin: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['goHome'])

const showModal = ref(false)
const currentIndex = ref(0)
const isEditMode = ref(false)

const announcements = ref([
  {
    icon: '🎓',
    title: '开学通知',
    content: '2024年春季学期将于3月1日正式开学，请各位同学提前做好准备。新学期，新气象，让我们一起迎接美好的学习生活！',
    date: '2024-02-20'
  },
  {
    icon: '📚',
    title: '图书馆开放时间',
    content: '图书馆开放时间为周一至周五 8:00-22:00，周末 9:00-21:00。欢迎同学们前来借阅图书，享受阅读的乐趣。',
    date: '2024-02-18'
  },
  {
    icon: '🏃',
    title: '体育设施开放',
    content: '体育馆、游泳池等体育设施已全面开放，欢迎同学们前来锻炼身体，增强体质，保持健康的生活方式。',
    date: '2024-02-15'
  },
  {
    icon: '🎉',
    title: '校园文化节',
    content: '一年一度的校园文化节即将拉开帷幕，届时将有丰富多彩的文艺演出、展览和互动活动，敬请期待！',
    date: '2024-02-10'
  },
  {
    icon: '💡',
    title: '创新创业大赛',
    content: '学校将举办创新创业大赛，鼓励同学们发挥创意，展示才华，优秀项目将获得奖金和创业支持。',
    date: '2024-02-08'
  },
  {
    icon: '⚠️',
    title: '安全提醒',
    content: '近期天气变化较大，请同学们注意保暖，预防感冒。同时请注意用电安全，遵守宿舍管理规定。',
    date: '2024-02-05'
  }
])

const images = ref([
  {
    url: 'https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=800&q=80',
    title: '校园图书馆',
    description: '现代化的图书馆，藏书丰富，环境优雅，是学习和阅读的理想场所。图书馆内设有多个阅览室、自习室和研讨室，为师生提供全方位的学习支持。'
  },
  {
    url: 'https://images.unsplash.com/photo-1562774053-701939374585?w=800&q=80',
    title: '教学楼',
    description: '宽敞明亮的教学楼，配备先进的教学设备，为师生提供优质的教学环境。每间教室都配备了多媒体设备，支持现代化的教学模式。'
  },
  {
    url: 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&q=80',
    title: '运动场',
    description: '标准化的运动场地，包括跑道、篮球场、足球场等，满足各种运动需求。运动场设施完善，是同学们锻炼身体的好去处。'
  },
  {
    url: 'https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=800&q=80',
    title: '学生宿舍',
    description: '舒适的学生宿舍，设施齐全，为学生提供温馨的居住环境。宿舍区配有洗衣房、自习室等公共设施，方便学生生活。'
  },
  {
    url: 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&q=80',
    title: '校园湖景',
    description: '美丽的校园湖泊，四季景色各异，是师生休闲放松的好去处。湖边设有步道和休息区，是晨读和散步的理想场所。'
  },
  {
    url: 'https://images.unsplash.com/photo-1564981797816-1043664bf78d?w=800&q=80',
    title: '实验楼',
    description: '设备先进的实验楼，配备各种专业实验室，支持科研和教学活动。实验室设施完善，为学生提供良好的实践平台。'
  },
  {
    url: 'https://images.unsplash.com/photo-1607237138185-eedd9c632b0b?w=800&q=80',
    title: '校园花园',
    description: '精心设计的校园花园，种植着各种花草树木，四季常青。花园是师生放松心情、享受自然美景的好地方。'
  },
  {
    url: 'https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=800&q=80',
    title: '学生活动中心',
    description: '多功能的学生活动中心，举办各种文艺演出、讲座和社团活动。活动中心设备齐全，为学生提供展示才华的舞台。'
  }
])

const news = ref([
  {
    icon: '📢',
    title: '学术讲座通知',
    content: '本周五下午3点，将在学术报告厅举办人工智能前沿技术讲座，欢迎感兴趣的同学参加。',
    time: '2小时前'
  },
  {
    icon: '🎓',
    title: '奖学金评定',
    content: '2024年春季学期奖学金评定工作即将开始，请符合条件的同学及时关注通知并准备相关材料。',
    time: '5小时前'
  },
  {
    icon: '🏃',
    title: '运动会报名',
    content: '年度运动会即将举行，各班级请于本周内完成运动员报名工作，展现班级风采。',
    time: '1天前'
  },
  {
    icon: '📚',
    title: '新书推荐',
    content: '图书馆新进一批优质图书，涵盖文学、科技、历史等多个领域，欢迎同学们前来借阅。',
    time: '2天前'
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

function toggleEditMode() {
  if (isEditMode.value) {
    saveChanges()
  }
  isEditMode.value = !isEditMode.value
}

function saveChanges() {
  localStorage.setItem('overview_announcements', JSON.stringify(announcements.value))
  localStorage.setItem('overview_images', JSON.stringify(images.value))
  localStorage.setItem('overview_news', JSON.stringify(news.value))
  alert('保存成功！')
}

function loadSavedData() {
  const savedAnnouncements = localStorage.getItem('overview_announcements')
  const savedImages = localStorage.getItem('overview_images')
  const savedNews = localStorage.getItem('overview_news')
  
  if (savedAnnouncements) announcements.value = JSON.parse(savedAnnouncements)
  if (savedImages) images.value = JSON.parse(savedImages)
  if (savedNews) news.value = JSON.parse(savedNews)
}

function addAnnouncement() {
  announcements.value.push({
    icon: '📢',
    title: '新公告',
    content: '请输入公告内容',
    date: new Date().toISOString().split('T')[0]
  })
}

function removeAnnouncement(index) {
  announcements.value.splice(index, 1)
}

function addImage() {
  images.value.push({
    url: 'https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=800&q=80',
    title: '新图片',
    description: '请输入图片描述'
  })
}

function removeImage(index) {
  images.value.splice(index, 1)
}

function addNews() {
  news.value.push({
    icon: '📢',
    title: '新动态',
    content: '请输入动态内容',
    time: '刚刚'
  })
}

function removeNews(index) {
  news.value.splice(index, 1)
}

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

loadSavedData()
</script>

<style scoped>
.overview {
  max-width: 1600px;
  margin: 0 auto;
  padding: 24px;
}

.overview__header {
  margin-bottom: 32px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.overview__title {
  font-size: 36px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px;
}

.overview__subtitle {
  font-size: 18px;
  color: #64748b;
  margin: 0;
}

.edit-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.edit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.overview__content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.info-section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.add-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(240, 147, 251, 0.4);
}

.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 20px;
}

.info-card {
  display: flex;
  gap: 16px;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.info-card--editable {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.info-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
}

.info-card__icon {
  font-size: 36px;
  flex-shrink: 0;
}

.icon-selector {
  flex-shrink: 0;
}

.icon-select {
  font-size: 32px;
  padding: 8px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  cursor: pointer;
}

.info-card__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-card__title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.info-card__text {
  font-size: 14px;
  opacity: 0.9;
  margin: 0;
  line-height: 1.6;
}

.info-card__date {
  font-size: 12px;
  opacity: 0.7;
  margin: 0;
}

.gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
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

.gallery-item--editable {
  cursor: default;
}

.gallery-item:hover {
  transform: scale(1.02);
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

.edit-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
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
  font-size: 40px;
  flex-shrink: 0;
}

.stat-item__value {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 4px;
}

.stat-item__label {
  font-size: 14px;
  opacity: 0.9;
  margin: 0;
}

.news-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.news-item {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.news-item--editable {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.news-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.news-item__icon {
  font-size: 32px;
  flex-shrink: 0;
}

.news-item__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.news-item__title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.news-item__content-text {
  font-size: 14px;
  opacity: 0.9;
  margin: 0;
  line-height: 1.6;
}

.news-item__time {
  font-size: 12px;
  opacity: 0.7;
  margin: 0;
}

.edit-input {
  width: 100%;
  padding: 8px 12px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 14px;
  transition: border-color 0.2s ease;
}

.edit-input:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.6);
}

.edit-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.edit-input--title,
.edit-input--news-title {
  font-size: 16px;
  font-weight: 600;
}

.edit-input--text,
.edit-input--news-content {
  resize: vertical;
}

.edit-input--date,
.edit-input--time {
  width: auto;
  align-self: flex-start;
}

.edit-input--url,
.edit-input--img-title,
.edit-input--desc {
  background: rgba(0, 0, 0, 0.6);
  border-color: rgba(255, 255, 255, 0.4);
}

.delete-btn {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
  align-self: flex-start;
}

.delete-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.6);
}

.delete-btn--img,
.delete-btn--news {
  align-self: flex-end;
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

  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .overview__title {
    font-size: 28px;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
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