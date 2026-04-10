<template>
  <section class="page">
    <header class="head">
      <button class="back" type="button" @click="$emit('back')">返回</button>
      <div class="head-copy">
        <p class="eyebrow">Settings</p>
        <h2 class="title">账户设置</h2>
      </div>
    </header>

    <section class="profile-hero">
      <div class="avatar" aria-hidden="true">
        <img v-if="previewAvatar" class="avatar-img" :src="previewAvatar" alt="头像预览" />
        <span v-else>{{ user?.username?.charAt(0)?.toUpperCase() || '?' }}</span>
      </div>
      <div>
        <h3 class="hero-name">{{ user?.username }}</h3>
        <p class="hero-sub">用户 ID：{{ user?.id }}</p>
      </div>
    </section>

    <div class="grid">
      <section class="card">
        <p class="card-kicker">Identity</p>
        <h3 class="card-title">修改登录账号</h3>

        <label class="field">
          <span>新 ID</span>
          <input v-model.trim="nextUsername" class="input" type="text" placeholder="请输入新的登录 ID" :disabled="isBuiltinAdmin" />
        </label>

        <label class="field">
          <span>当前密码</span>
          <input v-model="usernamePassword" class="input" type="password" placeholder="用于验证身份" :disabled="isBuiltinAdmin" />
        </label>

        <button class="btn btn--primary" type="button" :disabled="usernameSaving || isBuiltinAdmin" @click="saveUsername">
          {{ usernameSaving ? '保存中…' : '保存账号' }}
        </button>
      </section>

      <section class="card">
        <p class="card-kicker">Avatar</p>
        <h3 class="card-title">更新头像</h3>

        <label class="field">
          <span>上传图片</span>
          <input class="input file" type="file" accept="image/*" :disabled="avatarSaving" @change="onPickAvatar" />
        </label>

        <div class="row">
          <button class="btn btn--ghost" type="button" :disabled="avatarSaving || !previewAvatar" @click="clearAvatar">移除</button>
          <button class="btn btn--primary" type="button" :disabled="avatarSaving || !previewAvatar" @click="saveAvatar">
            {{ avatarSaving ? '保存中…' : '保存头像' }}
          </button>
        </div>
      </section>

      <section class="card card--wide">
        <p class="card-kicker">Security</p>
        <h3 class="card-title">修改密码</h3>

        <div class="password-grid">
          <label class="field">
            <span>旧密码</span>
            <input v-model="oldPassword" class="input" type="password" placeholder="请输入旧密码" :disabled="isBuiltinAdmin" />
          </label>

          <label class="field">
            <span>新密码</span>
            <input v-model="newPassword" class="input" type="password" placeholder="至少 6 位" :disabled="isBuiltinAdmin" />
          </label>

          <label class="field">
            <span>确认新密码</span>
            <input v-model="confirmPassword" class="input" type="password" placeholder="再次输入新密码" :disabled="isBuiltinAdmin" />
          </label>
        </div>

        <button class="btn btn--primary" type="button" :disabled="passwordSaving || isBuiltinAdmin" @click="savePassword">
          {{ passwordSaving ? '保存中…' : '更新密码' }}
        </button>
      </section>
    </div>

    <p v-if="message" class="msg" :class="`msg--${messageType}`">{{ message }}</p>
    <p v-if="isBuiltinAdmin" class="tip">内置管理员账号不支持在此处修改 ID 或密码。</p>
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
      setMsg('账号已更新。', 'success')
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
    setMsg('已选择头像，点击“保存头像”后生效。', 'info')
  }
  reader.onerror = () => setMsg('读取图片失败。', 'error')
  reader.readAsDataURL(file)
}

function clearAvatar() {
  previewAvatar.value = ''
  setMsg('头像已移除，点击“保存头像”后生效。', 'info')
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
  max-width: 1120px;
  margin: 0 auto;
  padding: 32px 18px 120px;
}

.head {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 18px;
}

.back {
  border: 0;
  min-height: 44px;
  padding: 0 16px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  color: #183b4d;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  box-shadow: 0 14px 30px rgba(20, 29, 41, 0.08);
}

.eyebrow,
.card-kicker {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(24, 59, 77, 0.58);
}

.title,
.card-title {
  margin: 0;
  line-height: 1.04;
  letter-spacing: -0.05em;
  color: #152131;
}

.title {
  font-size: clamp(30px, 4vw, 48px);
}

.profile-hero {
  border-radius: 30px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(24, 33, 47, 0.08);
  box-shadow: 0 24px 64px rgba(20, 29, 41, 0.08);
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar {
  width: 78px;
  height: 78px;
  border-radius: 24px;
  overflow: hidden;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, #e2c58f, #b78b4a);
  color: #152131;
  font-size: 28px;
  font-weight: 900;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hero-name {
  margin: 0;
  font-size: 30px;
  line-height: 1;
  letter-spacing: -0.05em;
  color: #152131;
}

.hero-sub {
  margin: 8px 0 0;
  color: rgba(24, 33, 47, 0.58);
}

.grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.card {
  border-radius: 28px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(24, 33, 47, 0.08);
  box-shadow: 0 24px 64px rgba(20, 29, 41, 0.08);
}

.card--wide {
  grid-column: 1 / -1;
}

.card-title {
  font-size: 30px;
}

.field {
  display: grid;
  gap: 8px;
  margin-top: 16px;
}

.field span {
  font-size: 13px;
  font-weight: 700;
  color: rgba(24, 33, 47, 0.66);
}

.input {
  min-height: 54px;
  border-radius: 18px;
  border: 1px solid rgba(24, 33, 47, 0.1);
  background: rgba(255, 255, 255, 0.84);
  padding: 0 16px;
  color: #18212f;
  outline: none;
}

.file {
  padding-top: 14px;
}

.password-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.row {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}

.btn {
  min-height: 54px;
  padding: 0 18px;
  border-radius: 18px;
  border: 0;
  font-size: 14px;
  font-weight: 800;
}

.btn--primary {
  background: linear-gradient(135deg, #183b4d, #29546c);
  color: #f8f4ec;
}

.btn--ghost {
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
}

.msg,
.tip {
  margin-top: 16px;
  padding: 14px 16px;
  border-radius: 18px;
  font-size: 14px;
  font-weight: 700;
}

.msg--success {
  background: rgba(17, 97, 73, 0.1);
  color: #116149;
}

.msg--error {
  background: rgba(154, 47, 39, 0.1);
  color: #9a2f27;
}

.msg--info {
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
}

.tip {
  background: rgba(191, 133, 36, 0.1);
  color: #84581c;
}

@media (max-width: 900px) {
  .grid,
  .password-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .head,
  .profile-hero,
  .row {
    flex-direction: column;
    align-items: flex-start;
  }

  .row .btn {
    width: 100%;
  }
}
</style>
