<template>
  <section class="page">
    <header class="head">
      <button class="back" type="button" @click="$emit('back')">返回</button>
      <div>
        <p class="kicker">我的</p>
        <h2 class="title">设置</h2>
      </div>
      <div class="spacer" />
    </header>

    <div class="card">
      <div class="rowTop">
        <div class="avatar" aria-hidden="true">
          <img v-if="previewAvatar" class="avatarImg" :src="previewAvatar" alt="头像预览" />
          <span v-else>{{ user?.username?.charAt(0)?.toUpperCase() || '?' }}</span>
        </div>
        <div class="meta">
          <div class="name">{{ user?.username }}</div>
          <div class="sub">内部 ID：{{ user?.id }}</div>
        </div>
      </div>

      <div class="section">
        <div class="sectionTitle">ID（登录账号）</div>
        <div class="field">
          <label class="label">新 ID</label>
          <input v-model.trim="nextUsername" class="input" type="text" placeholder="请输入新的登录 ID" :disabled="isBuiltinAdmin" />
        </div>
        <div class="field">
          <label class="label">当前密码</label>
          <input v-model="usernamePassword" class="input" type="password" placeholder="用于验证身份" :disabled="isBuiltinAdmin" />
        </div>
        <button class="btn" type="button" :disabled="usernameSaving || isBuiltinAdmin" @click="saveUsername">
          {{ usernameSaving ? '保存中…' : '保存 ID' }}
        </button>
      </div>

      <div class="section">
        <div class="sectionTitle">头像</div>
        <div class="field">
          <label class="label">上传头像</label>
          <input class="file" type="file" accept="image/*" :disabled="avatarSaving" @change="onPickAvatar" />
        </div>
        <div class="row">
          <button class="btn ghost" type="button" :disabled="avatarSaving || !previewAvatar" @click="clearAvatar">移除头像</button>
          <button class="btn" type="button" :disabled="avatarSaving || !previewAvatar" @click="saveAvatar">
            {{ avatarSaving ? '保存中…' : '保存头像' }}
          </button>
        </div>
      </div>

      <div class="section">
        <div class="sectionTitle">密码</div>
        <div class="field">
          <label class="label">旧密码</label>
          <input v-model="oldPassword" class="input" type="password" placeholder="请输入旧密码" :disabled="isBuiltinAdmin" />
        </div>
        <div class="field">
          <label class="label">新密码</label>
          <input v-model="newPassword" class="input" type="password" placeholder="请输入新密码" :disabled="isBuiltinAdmin" />
        </div>
        <div class="field">
          <label class="label">确认新密码</label>
          <input v-model="confirmPassword" class="input" type="password" placeholder="再次输入新密码" :disabled="isBuiltinAdmin" />
        </div>
        <button class="btn" type="button" :disabled="passwordSaving || isBuiltinAdmin" @click="savePassword">
          {{ passwordSaving ? '保存中…' : '修改密码' }}
        </button>
      </div>

      <p v-if="message" class="msg" :class="`msg--${messageType}`">{{ message }}</p>
      <p v-if="isBuiltinAdmin" class="tip">内置管理员账号不支持在此处修改 ID/密码。</p>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { changePassword, updateUsername } from '../lib/api'

const props = defineProps({
  user: { type: Object, default: null }
})

const emit = defineEmits(['back', 'updated'])

const isBuiltinAdmin = computed(() => props.user?.id === 0 && props.user?.username === 'admin')

const nextUsername = ref('')
const usernamePassword = ref('')
const usernameSaving = ref(false)

const previewAvatar = ref('')
const avatarSaving = ref(false)

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const passwordSaving = ref(false)

const message = ref('')
const messageType = ref('info')

watch(
  () => props.user,
  (u) => {
    nextUsername.value = u?.username || ''
    previewAvatar.value = u?.avatar || ''
  },
  { immediate: true }
)

function setMsg(text, type = 'info') {
  message.value = text
  messageType.value = type
}

async function saveUsername() {
  const username = nextUsername.value?.trim()
  const password = usernamePassword.value
  if (!props.user?.id) return
  if (!username) return setMsg('ID 不能为空。', 'error')
  if (!password) return setMsg('请输入当前密码用于验证。', 'error')
  if (username === props.user.username) return setMsg('ID 未变化。', 'info')

  usernameSaving.value = true
  setMsg('')
  try {
    const data = await updateUsername({ userId: props.user.id, password, username })
    if (data.code === 200) {
      emit('updated', { username })
      usernamePassword.value = ''
      setMsg('ID 已更新。', 'success')
      return
    }
    setMsg(data.msg || '保存失败。', 'error')
  } catch (err) {
    setMsg(`保存失败：${err?.message || '未知错误'}`, 'error')
  } finally {
    usernameSaving.value = false
  }
}

function onPickAvatar(e) {
  const file = e?.target?.files?.[0]
  if (!file) return
  if (!file.type?.startsWith('image/')) return setMsg('请选择图片文件。', 'error')
  const reader = new FileReader()
  reader.onload = () => {
    previewAvatar.value = String(reader.result || '')
    setMsg('已选择头像，点击“保存头像”生效。', 'info')
  }
  reader.onerror = () => setMsg('读取图片失败。', 'error')
  reader.readAsDataURL(file)
}

function clearAvatar() {
  previewAvatar.value = ''
  setMsg('头像已移除，点击“保存头像”生效。', 'info')
}

async function saveAvatar() {
  avatarSaving.value = true
  try {
    emit('updated', { avatar: previewAvatar.value || '' })
    setMsg('头像已更新。', 'success')
  } finally {
    avatarSaving.value = false
  }
}

async function savePassword() {
  if (!props.user?.id) return
  if (!oldPassword.value) return setMsg('请输入旧密码。', 'error')
  if (!newPassword.value) return setMsg('请输入新密码。', 'error')
  if (newPassword.value !== confirmPassword.value) return setMsg('两次输入的新密码不一致。', 'error')
  if (newPassword.value.length < 6) return setMsg('新密码至少 6 位。', 'error')

  passwordSaving.value = true
  setMsg('')
  try {
    const data = await changePassword({ userId: props.user.id, oldPassword: oldPassword.value, newPassword: newPassword.value })
    if (data.code === 200) {
      oldPassword.value = ''
      newPassword.value = ''
      confirmPassword.value = ''
      setMsg('密码已更新。', 'success')
      return
    }
    setMsg(data.msg || '修改失败。', 'error')
  } catch (err) {
    setMsg(`修改失败：${err?.message || '未知错误'}`, 'error')
  } finally {
    passwordSaving.value = false
  }
}
</script>

<style scoped>
.page {
  padding: 18px 16px 42px;
  max-width: 560px;
  margin: 0 auto;
}

.head {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: end;
  gap: 12px;
  margin-bottom: 14px;
}

.spacer {
  width: 48px;
}

.back {
  border: 0;
  border-radius: 14px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.06);
  color: rgba(15, 23, 42, 0.78);
  font-weight: 900;
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

.card {
  width: 100%;
  max-width: 560px;
  margin: 0 auto;
  border-radius: 20px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.66);
  border: 1px solid rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.14);
}

.rowTop {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px dashed rgba(0, 0, 0, 0.08);
}

.avatar {
  width: 52px;
  height: 52px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  font-weight: 1000;
  color: rgba(0, 95, 120, 1);
  background: linear-gradient(135deg, rgba(0, 168, 204, 0.18), rgba(254, 214, 227, 0.4));
  border: 1px solid rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.avatarImg {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.name {
  font-weight: 1000;
  color: rgba(15, 23, 42, 0.9);
}

.sub {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.6);
}

.section {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px dashed rgba(0, 0, 0, 0.08);
}

.sectionTitle {
  font-weight: 1000;
  color: rgba(15, 23, 42, 0.88);
  margin-bottom: 10px;
}

.field {
  display: grid;
  gap: 6px;
  margin-bottom: 10px;
}

.label {
  font-size: 12px;
  color: rgba(15, 23, 42, 0.6);
  font-weight: 900;
}

.input {
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.75);
  border-radius: 14px;
  padding: 11px 12px;
  font-weight: 700;
  color: rgba(15, 23, 42, 0.85);
}

.file {
  border: 1px dashed rgba(0, 0, 0, 0.16);
  background: rgba(255, 255, 255, 0.6);
  border-radius: 14px;
  padding: 10px 12px;
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.btn {
  width: 100%;
  border: 0;
  border-radius: 16px;
  padding: 12px 14px;
  font-weight: 1000;
  background: rgba(0, 168, 204, 0.22);
  border: 1px solid rgba(0, 168, 204, 0.28);
  color: rgba(0, 95, 120, 1);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ghost {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.06);
  color: rgba(15, 23, 42, 0.78);
}

.msg {
  margin: 12px 0 0;
  font-size: 13px;
  font-weight: 900;
}

.msg--success {
  color: #16a34a;
}

.msg--error {
  color: #dc2626;
}

.msg--info {
  color: rgba(15, 23, 42, 0.72);
}

.tip {
  margin: 10px 0 0;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.55);
}
</style>
