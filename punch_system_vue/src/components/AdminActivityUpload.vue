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

    <div v-if="message" class="notice" :class="`notice--${messageType}`">{{ message }}</div>

    <section v-if="isSuperAdmin && pendingReviews.length" class="queueSection">
      <div class="sectionHead">
        <div>
          <p class="sectionEyebrow">Pending Review</p>
          <h3 class="sectionTitle">待审批活动</h3>
        </div>
      </div>

      <div class="queueList">
        <article v-for="item in pendingReviews" :key="`pending-${item.dbId}`" class="queueCard">
          <div class="queueCard__main">
            <div class="queueCard__top">
              <span class="statusBadge statusBadge--pending">待审批</span>
              <span class="queueMeta">{{ item.category || '日常活动' }}</span>
            </div>
            <h4 class="queueTitle">{{ item.title }}</h4>
            <p class="queueText">{{ item.summary || item.tagline || '待审批活动内容' }}</p>
          </div>
          <div class="queueActions">
            <button class="smallBtn smallBtn--muted" type="button" :disabled="processingId === item.dbId" @click="reject(item)">
              {{ processingId === item.dbId ? '处理中' : '驳回' }}
            </button>
            <button class="smallBtn" type="button" :disabled="processingId === item.dbId" @click="approve(item)">
              {{ processingId === item.dbId ? '处理中' : '通过' }}
            </button>
          </div>
        </article>
      </div>
    </section>

    <section v-if="!isSuperAdmin && submissions.length" class="queueSection">
      <div class="sectionHead">
        <div>
          <p class="sectionEyebrow">My Uploads</p>
          <h3 class="sectionTitle">我的投稿</h3>
        </div>
      </div>

      <div class="queueList">
        <article v-for="item in submissions" :key="`submission-${item.dbId}`" class="queueCard">
          <div class="queueCard__main">
            <div class="queueCard__top">
              <span class="statusBadge" :class="`statusBadge--${item.status}`">{{ statusText(item.status) }}</span>
              <span class="queueMeta">{{ item.category || '日常活动' }}</span>
            </div>
            <h4 class="queueTitle">{{ item.title }}</h4>
            <p class="queueText">{{ item.summary || item.tagline || '已提交到主席审批' }}</p>
          </div>
        </article>
      </div>
    </section>

    <div v-if="filteredApproved.length" class="grid">
      <article v-for="(activity, idx) in filteredApproved" :key="activity.id" class="card">
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

          <div class="cardActions">
            <span class="actionLabel">公开活动</span>
            <button
              v-if="isSuperAdmin"
              class="smallBtn smallBtn--muted"
              type="button"
              :disabled="processingId === activity.dbId"
              @click="remove(activity)"
            >
              {{ processingId === activity.dbId ? '处理中' : '删除' }}
            </button>
          </div>
        </div>
      </article>
    </div>

    <div v-else class="empty">
      <p class="emptyTitle">没有找到匹配内容</p>
      <p class="emptyText">试着换一个关键词。</p>
    </div>

    <button class="fab" type="button" aria-label="新增活动" title="新增活动" @click="openComposer">+</button>

    <teleport to="body">
      <div v-if="composerOpen" class="composerOverlay" @click="closeComposer">
        <section class="composerSheet" @click.stop>
          <div class="composerHead">
            <div>
              <p class="composerEyebrow">New Activity</p>
              <h3 class="composerTitle">新建活动</h3>
            </div>
            <button class="composerClose" type="button" aria-label="关闭" @click="closeComposer">×</button>
          </div>

          <div class="editorMeta">
            <div class="formGrid">
              <label class="field">
                <span class="fieldLabel">活动名称</span>
                <input v-model.trim="form.title" class="editorInput" placeholder="请输入活动名称" />
              </label>

              <label class="field">
                <span class="fieldLabel">分类</span>
                <input v-model.trim="form.category" class="editorInput" placeholder="如：学习成长" />
              </label>

              <label class="field">
                <span class="fieldLabel">执行频率</span>
                <input v-model.trim="form.frequency" class="editorInput" placeholder="如：每日" />
              </label>

              <label class="field">
                <span class="fieldLabel">时长</span>
                <input v-model.trim="form.duration" class="editorInput" placeholder="如：10-20 分钟" />
              </label>

              <label class="field">
                <span class="fieldLabel">难度</span>
                <input v-model.trim="form.difficulty" class="editorInput" placeholder="如：轻松" />
              </label>

              <label class="field">
                <span class="fieldLabel">适合场景</span>
                <input v-model.trim="form.scene" class="editorInput" placeholder="如：宿舍 / 校园" />
              </label>
            </div>

            <label class="field">
              <span class="fieldLabel">副标题</span>
              <input v-model.trim="form.tagline" class="editorInput" placeholder="一句简短说明" />
            </label>

            <label class="field">
              <span class="fieldLabel">摘要</span>
              <textarea v-model.trim="form.summary" class="editorTextarea" rows="3" placeholder="列表中展示的简要内容"></textarea>
            </label>

            <label class="field">
              <span class="fieldLabel">详细描述</span>
              <textarea v-model.trim="form.description" class="editorTextarea" rows="4" placeholder="详情页展示的完整描述"></textarea>
            </label>

            <div class="formGrid">
              <label class="field">
                <span class="fieldLabel">亮点</span>
                <textarea
                  v-model.trim="form.highlightsText"
                  class="editorTextarea"
                  rows="4"
                  placeholder="每行一条，或用逗号分隔"
                ></textarea>
              </label>

              <label class="field">
                <span class="fieldLabel">步骤</span>
                <textarea
                  v-model.trim="form.stepsText"
                  class="editorTextarea"
                  rows="4"
                  placeholder="每行一条，或用逗号分隔"
                ></textarea>
              </label>
            </div>

            <label class="field">
              <span class="fieldLabel">建议</span>
              <textarea
                v-model.trim="form.tipsText"
                class="editorTextarea"
                rows="4"
                placeholder="每行一条，或用逗号分隔"
              ></textarea>
            </label>

            <label class="field">
              <span class="fieldLabel">封面图片</span>
              <label class="fileTrigger">
                <input class="fileInput" type="file" accept="image/*" @change="onPick" />
                <span class="fileTrigger__button">选择图片</span>
                <span class="fileTrigger__text">{{ pickedFileName || '未选择文件' }}</span>
              </label>
            </label>

            <div v-if="form.coverImage" class="preview">
              <img class="previewImg" :src="form.coverImage" alt="预览图" />
            </div>

            <div class="actions">
              <button class="actionBtn" type="button" :disabled="saving" @click="save">
                {{ saving ? '提交中' : submitButtonText }}
              </button>
              <button class="actionBtn actionBtn--muted" type="button" :disabled="saving" @click="resetForm">重置表单</button>
            </div>
          </div>
        </section>
      </div>
    </teleport>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { approveActivity, createActivity, deleteActivity, getAdminActivities, rejectActivity } from '../lib/api'

const props = defineProps({
  token: { type: String, default: '' },
  role: { type: String, default: 'user' }
})

const emit = defineEmits(['changed'])

const keyword = ref('')
const pickedFileName = ref('')
const saving = ref(false)
const processingId = ref(null)
const message = ref('')
const messageType = ref('info')
const composerOpen = ref(false)

const approvedActivities = ref([])
const submissions = ref([])
const pendingReviews = ref([])

const form = reactive({
  title: '',
  category: '',
  frequency: '',
  duration: '',
  difficulty: '',
  scene: '',
  tagline: '',
  summary: '',
  description: '',
  highlightsText: '',
  stepsText: '',
  tipsText: '',
  coverImage: ''
})

const isSuperAdmin = computed(() => props.role === 'super_admin')
const submitButtonText = computed(() => (isSuperAdmin.value ? '发布活动' : '提交审批'))

const filteredApproved = computed(() => {
  const q = keyword.value.toLowerCase()
  return approvedActivities.value.filter((item) => {
    if (!q) return true
    return [item.title, item.tagline, item.summary, item.scene, item.category, ...(item.highlights || [])]
      .filter(Boolean)
      .some((text) => String(text).toLowerCase().includes(q))
  })
})

function setMsg(text, type = 'info') {
  message.value = text
  messageType.value = type
}

function statusText(status) {
  if (status === 'approved') return '已通过'
  if (status === 'rejected') return '已驳回'
  return '待审批'
}

function normalizeLines(text) {
  return String(text || '')
    .split(/\n|,|，/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function resetForm() {
  form.title = ''
  form.category = ''
  form.frequency = ''
  form.duration = ''
  form.difficulty = ''
  form.scene = ''
  form.tagline = ''
  form.summary = ''
  form.description = ''
  form.highlightsText = ''
  form.stepsText = ''
  form.tipsText = ''
  form.coverImage = ''
  pickedFileName.value = ''
}

function openComposer() {
  composerOpen.value = true
}

function closeComposer() {
  composerOpen.value = false
}

function onPick(e) {
  const file = e?.target?.files?.[0]
  if (!file) return
  pickedFileName.value = file.name
  const reader = new FileReader()
  reader.onload = () => {
    form.coverImage = String(reader.result || '')
  }
  reader.readAsDataURL(file)
}

async function loadAdminData() {
  if (!props.token) return
  try {
    const data = await getAdminActivities({ token: props.token })
    if (data.code === 200) {
      approvedActivities.value = data.approved || []
      submissions.value = data.submissions || []
      pendingReviews.value = data.pending_reviews || []
    }
  } catch (err) {
    setMsg(`加载活动失败：${err?.message || '未知错误'}`, 'error')
  }
}

async function save() {
  if (!props.token) return setMsg('缺少登录凭证。', 'error')
  if (!form.title.trim()) return setMsg('活动名称不能为空。', 'error')

  saving.value = true
  setMsg('')
  try {
    const data = await createActivity({
      token: props.token,
      title: form.title,
      category: form.category,
      frequency: form.frequency,
      duration: form.duration,
      difficulty: form.difficulty,
      scene: form.scene,
      tagline: form.tagline,
      summary: form.summary,
      description: form.description,
      highlights: normalizeLines(form.highlightsText),
      steps: normalizeLines(form.stepsText),
      tips: normalizeLines(form.tipsText),
      cover_image: form.coverImage
    })
    if (data.code === 200) {
      resetForm()
      closeComposer()
      setMsg(data.msg || '活动已保存。', 'success')
      await loadAdminData()
      emit('changed')
      return
    }
    setMsg(data.msg || '保存失败。', 'error')
  } catch (err) {
    setMsg(`保存失败：${err?.message || '未知错误'}`, 'error')
  } finally {
    saving.value = false
  }
}

async function approve(item) {
  if (!props.token || !item?.dbId) return
  processingId.value = item.dbId
  setMsg('')
  try {
    const data = await approveActivity({ token: props.token, activityId: item.dbId })
    if (data.code === 200) {
      setMsg(data.msg || '活动已通过审批。', 'success')
      await loadAdminData()
      emit('changed')
      return
    }
    setMsg(data.msg || '审批失败。', 'error')
  } catch (err) {
    setMsg(`审批失败：${err?.message || '未知错误'}`, 'error')
  } finally {
    processingId.value = null
  }
}

async function reject(item) {
  if (!props.token || !item?.dbId) return
  processingId.value = item.dbId
  setMsg('')
  try {
    const data = await rejectActivity({ token: props.token, activityId: item.dbId })
    if (data.code === 200) {
      setMsg(data.msg || '活动已驳回。', 'success')
      await loadAdminData()
      return
    }
    setMsg(data.msg || '驳回失败。', 'error')
  } catch (err) {
    setMsg(`驳回失败：${err?.message || '未知错误'}`, 'error')
  } finally {
    processingId.value = null
  }
}

async function remove(activity) {
  if (!props.token || !activity?.dbId) return
  if (!confirm(`确定删除“${activity.title}”吗？`)) return

  processingId.value = activity.dbId
  setMsg('')
  try {
    const data = await deleteActivity({ token: props.token, activityId: activity.dbId })
    if (data.code === 200) {
      setMsg(data.msg || '活动已删除。', 'success')
      await loadAdminData()
      emit('changed')
      return
    }
    setMsg(data.msg || '删除失败。', 'error')
  } catch (err) {
    setMsg(`删除失败：${err?.message || '未知错误'}`, 'error')
  } finally {
    processingId.value = null
  }
}

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

onMounted(() => {
  loadAdminData()
})
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

.eyebrow,
.sectionEyebrow,
.composerEyebrow {
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
  box-sizing: border-box;
}

.notice {
  margin-bottom: 16px;
  padding: 12px 14px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 800;
}

.notice--success {
  background: rgba(34, 197, 94, 0.12);
  color: #166534;
}

.notice--error {
  background: rgba(239, 68, 68, 0.12);
  color: #991b1b;
}

.queueSection {
  margin-bottom: 18px;
  padding: 20px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(24, 33, 47, 0.08);
  box-shadow: 0 18px 42px rgba(20, 29, 41, 0.06);
}

.sectionHead {
  margin-bottom: 14px;
}

.sectionTitle {
  margin: 0;
  font-size: 26px;
  line-height: 1.02;
  letter-spacing: -0.05em;
  color: #152131;
}

.queueList {
  display: grid;
  gap: 12px;
}

.queueCard {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding: 16px;
  border-radius: 22px;
  background: rgba(248, 242, 231, 0.6);
  border: 1px solid rgba(24, 33, 47, 0.06);
}

.queueCard__main {
  min-width: 0;
}

.queueCard__top {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.queueMeta {
  font-size: 12px;
  color: rgba(24, 33, 47, 0.56);
  font-weight: 700;
}

.queueTitle {
  margin: 10px 0 0;
  font-size: 18px;
  color: #152131;
}

.queueText {
  margin: 8px 0 0;
  color: rgba(24, 33, 47, 0.66);
  line-height: 1.7;
}

.queueActions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
}

.statusBadge {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
}

.statusBadge--pending {
  background: rgba(245, 158, 11, 0.14);
  color: #b45309;
}

.statusBadge--approved {
  background: rgba(34, 197, 94, 0.14);
  color: #166534;
}

.statusBadge--rejected {
  background: rgba(239, 68, 68, 0.14);
  color: #991b1b;
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

.cover::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(7, 13, 22, 0.18)),
    radial-gradient(circle at 78% 18%, rgba(255, 255, 255, 0.18), transparent 24%);
}

.coverImage {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
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

.cardActions,
.actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 16px;
}

.actionLabel,
.actionBtn,
.smallBtn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 0 14px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.actionLabel {
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
}

.actionBtn,
.smallBtn {
  border: 0;
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
  cursor: pointer;
}

.actionBtn--muted,
.smallBtn--muted {
  background: rgba(215, 177, 120, 0.14);
  color: #805c20;
}

.actionBtn:disabled,
.smallBtn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
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

.fab {
  position: fixed;
  right: max(18px, calc((100vw - min(1120px, 100vw)) / 2 + 18px));
  bottom: calc(96px + env(safe-area-inset-bottom, 0px));
  width: 58px;
  height: 58px;
  border-radius: 999px;
  border: 0;
  background: linear-gradient(145deg, #d7b178, #b78b4a);
  color: #fffdf8;
  font-size: 34px;
  line-height: 1;
  box-shadow: 0 20px 42px rgba(183, 139, 74, 0.32);
  z-index: 30;
}

.composerOverlay {
  position: fixed;
  inset: 0;
  z-index: 80;
  background: rgba(15, 23, 42, 0.28);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 14px;
  box-sizing: border-box;
}

.composerSheet {
  width: min(880px, 100%);
  max-height: min(84vh, 920px);
  overflow-y: auto;
  border-radius: 28px 28px 0 0;
  background: rgba(255, 252, 247, 0.98);
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.22);
  padding: 18px;
  box-sizing: border-box;
}

.composerHead {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.composerTitle {
  margin: 0;
  font-size: 30px;
  line-height: 1;
  letter-spacing: -0.05em;
  color: #152131;
}

.composerClose {
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 999px;
  background: rgba(24, 33, 47, 0.06);
  color: rgba(24, 33, 47, 0.7);
  font-size: 24px;
  line-height: 1;
}

.editorMeta {
  display: grid;
  gap: 14px;
}

.formGrid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.field {
  display: grid;
  gap: 8px;
}

.fieldLabel {
  font-size: 12px;
  font-weight: 700;
  color: rgba(24, 33, 47, 0.62);
}

.editorInput,
.editorTextarea,
.fileTrigger {
  width: 100%;
  border-radius: 16px;
  border: 1px solid rgba(24, 33, 47, 0.08);
  background: rgba(255, 255, 255, 0.76);
  padding: 12px 14px;
  font-size: 14px;
  color: #18212f;
  outline: none;
  box-sizing: border-box;
}

.editorTextarea {
  resize: vertical;
  min-height: 96px;
}

.fileTrigger {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 48px;
  cursor: pointer;
}

.fileInput {
  display: none;
}

.fileTrigger__button {
  flex-shrink: 0;
  min-height: 30px;
  padding: 0 10px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  background: rgba(215, 177, 120, 0.18);
  color: #183b4d;
  font-size: 12px;
  font-weight: 800;
}

.fileTrigger__text {
  min-width: 0;
  color: rgba(24, 33, 47, 0.62);
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.preview {
  overflow: hidden;
  border-radius: 18px;
}

.previewImg {
  width: 100%;
  max-height: 240px;
  object-fit: cover;
  display: block;
}

@media (max-width: 900px) {
  .grid,
  .formGrid {
    grid-template-columns: 1fr;
  }

  .queueCard,
  .queueActions,
  .cardActions,
  .actions {
    display: grid;
    grid-template-columns: 1fr;
  }

  .fab {
    right: 14px;
    bottom: calc(92px + env(safe-area-inset-bottom, 0px));
    width: 54px;
    height: 54px;
    font-size: 30px;
  }

  .composerSheet {
    padding: 16px 14px calc(16px + env(safe-area-inset-bottom, 0px));
  }

  .composerTitle,
  .sectionTitle {
    font-size: 26px;
  }
}
</style>
