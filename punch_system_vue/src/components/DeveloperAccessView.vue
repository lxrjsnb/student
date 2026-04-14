<template>
  <section class="page">
    <header class="hero">
      <button class="back" type="button" aria-label="返回" title="返回" @click="$emit('back')">‹</button>
      <div class="heroCopy">
        <p class="eyebrow">Developer</p>
        <h2 class="title">开发者权限</h2>
        <p class="subtitle">支持按账号搜索、按角色筛选，并为指定用户执行密码重置。</p>
      </div>
    </header>

    <section class="panel">
      <div class="toolbar">
        <label class="searchField searchField--inline">
          <span class="fieldLabel">搜索</span>
          <div class="searchInline">
            <input
              v-model.trim="keyword"
              class="fieldControl"
              type="search"
              placeholder="搜索姓名、账号、学号、班级、部门、电话"
              @input="scheduleLoad"
            />
            <button class="refreshBtn toolbarBtn" type="button" :disabled="loading" @click="loadUsers">
              {{ loading ? '加载中…' : '刷新' }}
            </button>
          </div>
        </label>
      </div>

      <p v-if="message" class="notice" :class="`notice--${messageType}`">{{ message }}</p>

      <div v-if="users.length" class="cardsGrid">
        <button
          v-for="user in users"
          :key="user.id"
          class="userCardButton"
          type="button"
          @click="openEditor(user)"
        >
          <article class="userCard">
            <header class="cardHead">
              <div class="identityBlock">
                <h3 class="identityName">{{ user.nickname || user.username || '未命名用户' }}</h3>
                <div class="identityMeta">
                  <span class="pill" :class="user.is_online ? 'pill--ok' : 'pill--muted'">{{ user.is_online ? '在线' : '离线' }}</span>
                  <span v-if="user.student_no" class="metaChip">学号 {{ user.student_no }}</span>
                  <span v-if="user.class_name" class="metaChip">班级 {{ user.class_name }}</span>
                  <span v-if="user.department" class="metaChip">部门 {{ user.department }}</span>
                </div>
              </div>
            </header>

            <footer class="cardFoot">
              <div class="metaGroup">
                <span class="metaLabel">最近登录</span>
                <span class="metaValue">{{ user.last_login_at || '-' }}</span>
              </div>
              <div class="metaGroup">
                <span class="metaLabel">当前角色</span>
                <span class="metaValue">{{ roleLabel(user.role) }}</span>
              </div>
            </footer>
          </article>
        </button>
      </div>
      <div v-else class="emptyState">{{ loading ? '正在加载…' : '暂无用户数据' }}</div>
    </section>

    <transition name="sheet">
      <div v-if="editingUser" class="sheetOverlay" @click.self="closeEditor">
        <section class="sheetPanel">
          <div class="sheetHandle" aria-hidden="true"></div>

          <header class="sheetHeader">
            <div>
              <p class="sheetEyebrow">编辑用户</p>
              <h3 class="sheetTitle">{{ editingUser.nickname || editingUser.username || '未命名用户' }}</h3>
            </div>
            <button class="sheetClose" type="button" aria-label="关闭" @click="closeEditor">✕</button>
          </header>

          <div class="sheetMeta">
            <span class="pill" :class="editingUser.is_online ? 'pill--ok' : 'pill--muted'">{{ editingUser.is_online ? '在线' : '离线' }}</span>
            <span class="metaChip">账号 {{ editingUser.username || '-' }}</span>
          </div>

          <div class="sheetBody">
            <div class="fieldsGrid">
              <label class="fieldCard">
                <span class="fieldCard__label">姓名</span>
                <input v-model.trim="editingUser.nickname" class="tableInput" type="text" placeholder="姓名" />
              </label>

              <label class="fieldCard">
                <span class="fieldCard__label">学号</span>
                <input v-model.trim="editingUser.student_no" class="tableInput" type="text" placeholder="学号" />
              </label>

              <label class="fieldCard">
                <span class="fieldCard__label">班级</span>
                <input v-model.trim="editingUser.class_name" class="tableInput" type="text" placeholder="班级" />
              </label>

              <label class="fieldCard">
                <span class="fieldCard__label">部门</span>
                <input v-model.trim="editingUser.department" class="tableInput" type="text" placeholder="部门" />
              </label>

              <label class="fieldCard">
                <span class="fieldCard__label">电话号</span>
                <input v-model.trim="editingUser.phone" class="tableInput" type="text" placeholder="电话号" />
              </label>

              <label class="fieldCard">
                <span class="fieldCard__label">角色</span>
                <select v-model="editingUser.role" class="tableInput tableInput--select">
                  <option value="user">部员</option>
                  <option value="admin">部长</option>
                  <option value="super_admin">主席</option>
                </select>
              </label>

              <label class="fieldCard fieldCard--wide">
                <span class="fieldCard__label">密码重置</span>
                <input v-model.trim="editingUser.draftPassword" class="tableInput" type="password" placeholder="输入新密码后保存" />
              </label>
            </div>
          </div>

          <footer class="sheetFooter">
            <p class="note">密码需符合系统当前密码规则，留空则保持不变；电话号按数据库字段长度直接保存。</p>
            <div class="sheetActions">
              <button class="ghostAction" type="button" :disabled="savingId === editingUser.id" @click="closeEditor">取消</button>
              <button class="saveBtn" type="button" :disabled="savingId === editingUser.id" @click="saveUser(editingUser)">
                {{ savingId === editingUser.id ? '保存中…' : '保存' }}
              </button>
            </div>
          </footer>
        </section>
      </div>
    </transition>
  </section>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { getDeveloperUsers, updateDeveloperUser } from '../lib/api'

const props = defineProps({
  token: { type: String, required: true },
  currentUserId: { type: Number, default: 0 }
})

const emit = defineEmits(['back', 'updated'])

const loading = ref(false)
const savingId = ref(0)
const keyword = ref('')
const users = ref([])
const editingUser = ref(null)
const message = ref('')
const messageType = ref('info')

let searchTimer = null
const ROLE_LABELS = {
  user: '部员',
  admin: '部长',
  super_admin: '主席'
}

function toEditableUser(user = {}) {
  return {
    id: user.id,
    username: user.username || '',
    nickname: user.nickname || '',
    student_no: user.student_no || '',
    class_name: user.class_name || '',
    department: user.department || '',
    phone: user.phone || '',
    role: user.role || 'user',
    is_online: Boolean(user.is_online),
    last_login_at: user.last_login_at || '',
    draftPassword: ''
  }
}

function setNotice(text, type = 'info') {
  message.value = text
  messageType.value = type
}

function roleLabel(role) {
  return ROLE_LABELS[role] || role || '-'
}

async function loadUsers() {
  if (!props.token) return

  loading.value = true
  try {
    const data = await getDeveloperUsers({
      token: props.token,
      keyword: keyword.value
    })
    if (data.code === 200) {
      users.value = (data.data || []).map(toEditableUser)
      if (messageType.value !== 'error') {
        setNotice('', 'info')
      }
    } else {
      setNotice(data.msg || '加载失败', 'error')
    }
  } catch (err) {
    setNotice(err?.message || '加载失败', 'error')
  } finally {
    loading.value = false
  }
}

function scheduleLoad() {
  if (searchTimer) window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(() => {
    loadUsers()
  }, 250)
}

function openEditor(user) {
  editingUser.value = toEditableUser(user)
}

function closeEditor() {
  if (savingId.value) return
  editingUser.value = null
}

async function saveUser(user) {
  if (!props.token) return

  savingId.value = user.id
  try {
    const data = await updateDeveloperUser({
      token: props.token,
      userId: user.id,
      payload: {
        nickname: user.nickname,
        student_no: user.student_no,
        class_name: user.class_name,
        department: user.department,
        phone: user.phone,
        password: user.draftPassword,
        role: user.role
      }
    })

    if (data.code !== 200) {
      setNotice(data.msg || '保存失败', 'error')
      return
    }

    const nextUser = toEditableUser(data.data || user)
    users.value = users.value.map((item) => (item.id === user.id ? nextUser : item))
    editingUser.value = null
    setNotice(`用户 ${user.username || user.id} 已更新`, 'success')

    if (Number(user.id) === Number(props.currentUserId) && data.data) {
      emit('updated', data.data)
    }
  } catch (err) {
    setNotice(err?.message || '保存失败', 'error')
  } finally {
    savingId.value = 0
  }
}

onMounted(() => {
  loadUsers()
})

onBeforeUnmount(() => {
  if (searchTimer) window.clearTimeout(searchTimer)
})
</script>

<style scoped>
.page {
  max-width: 1360px;
  margin: 0 auto;
  padding: 28px 18px 120px;
}

.panel {
  border-radius: 28px;
  border: 1px solid rgba(24, 33, 47, 0.08);
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 22px 54px rgba(20, 29, 41, 0.08);
}

.hero {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 16px;
  align-items: center;
  padding: 0 0 6px;
}

.back,
.refreshBtn,
.saveBtn {
  appearance: none;
  border: 0;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.back {
  border-radius: 16px;
  width: 48px;
  min-height: 46px;
  padding: 0;
  font-size: 32px;
  line-height: 1;
  color: #183b4d;
  background: rgba(24, 59, 77, 0.08);
}

.saveBtn {
  border-radius: 16px;
  min-height: 46px;
  padding: 0 16px;
  color: #fff;
  background: linear-gradient(135deg, #183b4d, #2c5f77);
}

.refreshBtn {
  min-height: 38px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
  font-size: 12px;
  font-weight: 800;
  align-self: end;
  transition: transform 0.18s ease, background 0.18s ease;
}

.refreshBtn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.toolbarBtn {
  white-space: nowrap;
}

.eyebrow {
  margin: 0;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(24, 59, 77, 0.54);
}

.title {
  margin: 8px 0 0;
  font-size: clamp(28px, 4vw, 44px);
  line-height: 1;
  letter-spacing: -0.05em;
  color: #152131;
}

.subtitle {
  margin: 10px 0 0;
  max-width: 760px;
  color: rgba(24, 33, 47, 0.62);
  font-size: 14px;
}

.panel {
  margin-top: 18px;
  padding: 20px;
}

.toolbar {
  margin-bottom: 16px;
}

.searchField--inline {
  min-width: 0;
}

.searchInline {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
}

.searchField,
.filterField {
  display: grid;
  gap: 6px;
}

.fieldLabel {
  font-size: 12px;
  font-weight: 700;
  color: rgba(24, 33, 47, 0.62);
}

.fieldControl,
.tableInput {
  width: 100%;
  border: 1px solid rgba(24, 33, 47, 0.12);
  border-radius: 14px;
  padding: 12px 14px;
  background: #fff;
  color: #152131;
  font: inherit;
}

.tableInput {
  min-width: 124px;
  padding: 10px 12px;
  border-radius: 12px;
}

.tableInput--select {
  min-width: 140px;
}

.notice {
  margin: 0 0 14px;
  padding: 12px 14px;
  border-radius: 16px;
  font-size: 14px;
}

.notice--success {
  background: rgba(42, 111, 78, 0.12);
  color: #21533a;
}

.notice--error {
  background: rgba(170, 64, 54, 0.12);
  color: #8e2d24;
}

.notice--info {
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
}

.cardsGrid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.userCardButton {
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
  font: inherit;
  color: inherit;
  cursor: pointer;
}

.userCard {
  border-radius: 24px;
  border: 1px solid rgba(24, 33, 47, 0.08);
  background:
    radial-gradient(circle at top right, rgba(226, 197, 143, 0.18), transparent 32%),
    linear-gradient(180deg, rgba(251, 252, 249, 0.98), rgba(244, 247, 240, 0.9));
  padding: 18px;
  box-shadow: 0 18px 36px rgba(20, 29, 41, 0.05);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.userCardButton:hover .userCard,
.userCardButton:focus-visible .userCard {
  transform: translateY(-2px);
  box-shadow: 0 22px 40px rgba(20, 29, 41, 0.08);
}

.userCardButton:focus-visible {
  outline: none;
}

.cardHead,
.cardFoot {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.cardHead {
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(24, 33, 47, 0.08);
}

.cardFoot {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid rgba(24, 33, 47, 0.08);
}

.identityBlock {
  min-width: 0;
}

.identityName {
  margin: 0;
  font-size: 26px;
  line-height: 1;
  letter-spacing: -0.05em;
  color: #152131;
}

.note,
.emptyState {
  color: rgba(24, 33, 47, 0.62);
  font-size: 13px;
}

.identityMeta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.metaChip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
  font-size: 12px;
  font-weight: 700;
}

.pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  width: fit-content;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.pill--ok {
  background: rgba(42, 111, 78, 0.12);
  color: #21533a;
}

.pill--muted {
  background: rgba(24, 33, 47, 0.08);
  color: rgba(24, 33, 47, 0.62);
}

.fieldsGrid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.fieldCard {
  display: grid;
  gap: 6px;
}

.fieldCard--wide {
  grid-column: 1 / -1;
}

.fieldCard__label,
.metaLabel {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(24, 59, 77, 0.56);
}

.metaGroup {
  display: grid;
  gap: 6px;
}

.metaValue {
  font-size: 14px;
  font-weight: 600;
  color: #152131;
}

.saveBtn--row {
  min-height: 40px;
  padding: 0 14px;
}

.sheetOverlay {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 16px;
  background: rgba(20, 29, 41, 0.28);
  backdrop-filter: blur(8px);
}

.sheetPanel {
  width: min(760px, 100%);
  max-height: min(84vh, 920px);
  border-radius: 28px 28px 0 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 249, 244, 0.98));
  box-shadow: 0 30px 60px rgba(20, 29, 41, 0.18);
  overflow: hidden;
}

.sheetHandle {
  width: 52px;
  height: 6px;
  margin: 12px auto 0;
  border-radius: 999px;
  background: rgba(24, 59, 77, 0.16);
}

.sheetHeader,
.sheetFooter {
  padding: 18px 20px;
}

.sheetHeader {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.sheetEyebrow {
  margin: 0 0 6px;
  color: rgba(24, 59, 77, 0.56);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.sheetTitle {
  margin: 0;
  color: #152131;
  font-size: 28px;
  line-height: 1;
}

.sheetClose,
.ghostAction {
  appearance: none;
  border: 0;
  font: inherit;
  cursor: pointer;
}

.sheetClose {
  width: 40px;
  min-width: 40px;
  height: 40px;
  border-radius: 999px;
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
  font-size: 16px;
}

.sheetMeta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 0 20px 16px;
}

.sheetBody {
  max-height: calc(84vh - 212px);
  padding: 0 20px 12px;
  overflow: auto;
}

.sheetFooter {
  display: grid;
  gap: 12px;
  border-top: 1px solid rgba(24, 33, 47, 0.08);
  background: rgba(255, 255, 255, 0.9);
}

.sheetActions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.ghostAction {
  min-height: 46px;
  padding: 0 16px;
  border-radius: 16px;
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
  font-weight: 700;
}

.sheet-enter-active,
.sheet-leave-active {
  transition: opacity 0.18s ease;
}

.sheet-enter-active .sheetPanel,
.sheet-leave-active .sheetPanel {
  transition: transform 0.22s ease;
}

.sheet-enter-from,
.sheet-leave-to {
  opacity: 0;
}

.sheet-enter-from .sheetPanel,
.sheet-leave-to .sheetPanel {
  transform: translateY(100%);
}

.emptyState {
  text-align: center;
  padding: 42px 16px;
  border-radius: 22px;
  border: 1px dashed rgba(24, 33, 47, 0.14);
  background: rgba(244, 247, 240, 0.74);
}

.note {
  margin: 14px 4px 0;
}

@media (max-width: 1120px) {
  .cardsGrid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .page {
    padding: 18px 12px 104px;
  }

  .hero {
    grid-template-columns: auto 1fr;
    gap: 12px;
    padding: 0 0 4px;
  }

  .toolbar {
    grid-template-columns: 1fr;
  }

  .searchInline {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .panel {
    padding: 16px;
  }

  .cardHead,
  .cardFoot {
    display: grid;
  }

  .fieldsGrid {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .userCard {
    padding: 16px;
    border-radius: 20px;
  }

  .identityName {
    font-size: 22px;
  }

  .cardFoot {
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    align-items: start;
  }

  .metaGroup {
    gap: 4px;
    min-width: 0;
  }

  .metaValue {
    font-size: 13px;
    word-break: break-word;
  }

  .sheetOverlay {
    padding: 0;
  }

  .sheetPanel {
    width: 100%;
    max-height: 88vh;
    border-radius: 24px 24px 0 0;
  }

  .sheetHeader,
  .sheetFooter,
  .sheetMeta,
  .sheetBody {
    padding-left: 16px;
    padding-right: 16px;
  }

  .sheetBody {
    max-height: calc(88vh - 212px);
  }

  .sheetActions {
    grid-template-columns: 1fr 1fr;
    display: grid;
  }
}
</style>
