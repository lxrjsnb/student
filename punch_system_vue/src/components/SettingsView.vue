<template>
  <section class="page">
    <header class="head">
      <button class="back" type="button" aria-label="返回" title="返回" @click="$emit('back')">‹</button>
      <div class="headCopy">
        <p class="eyebrow">Account</p>
        <h2 class="title">账户设置</h2>
      </div>
    </header>

    <div v-if="message" class="notice" :class="`notice--${messageType}`">
      {{ message }}
    </div>

    <div v-if="isBuiltinAdmin" class="notice notice--warn">
      内置管理员账号不支持在此处修改账号或密码。
    </div>

    <div class="layout">
      <section class="card">
        <div class="cardHead">
          <p class="cardKicker">Phone</p>
          <h3 class="cardTitle">修改手机号</h3>
          <p class="cardDesc">请输入新的 11 位手机号，并使用当前密码完成验证。提交后需经管理员审批，处理进度会显示在消息里。</p>
        </div>

        <label class="field">
          <span class="fieldLabel">新手机号</span>
          <input
            v-model.trim="nextPhone"
            class="input"
            type="tel"
            inputmode="numeric"
            placeholder="请输入 11 位手机号"
          />
        </label>

        <label class="field">
          <span class="fieldLabel">当前密码</span>
          <input
            v-model="phonePassword"
            class="input"
            type="password"
            placeholder="用于验证身份"
          />
        </label>

        <button class="btn btn--primary btn--submit" type="button" :disabled="phoneSaving" @click="savePhone">
          {{ phoneSaving ? '提交中…' : '提交申请' }}
        </button>
      </section>

      <section class="card card--wide">
        <div class="cardHead">
          <p class="cardKicker">Security</p>
          <h3 class="cardTitle">修改密码</h3>
          <p class="cardDesc">密码长度需为 8-64 位，且至少包含大写字母、小写字母和数字，不得包含账号、学号、手机号等个人信息。</p>
        </div>

        <div class="passwordGrid">
          <label class="field">
            <span class="fieldLabel">旧密码</span>
            <input
              v-model="oldPassword"
              class="input"
              type="password"
              placeholder="请输入旧密码"
              :disabled="isBuiltinAdmin"
            />
          </label>

          <label class="field">
            <span class="fieldLabel">新密码</span>
            <input
              v-model="newPassword"
              class="input"
              type="password"
              placeholder="8-64 位，且包含大小写字母和数字"
              :disabled="isBuiltinAdmin"
            />
          </label>

          <label class="field">
            <span class="fieldLabel">确认新密码</span>
            <input
              v-model="confirmPassword"
              class="input"
              type="password"
              placeholder="再次输入新密码"
              :disabled="isBuiltinAdmin"
            />
          </label>
        </div>

        <button class="btn btn--primary btn--submit" type="button" :disabled="passwordSaving || isBuiltinAdmin" @click="savePassword">
          {{ passwordSaving ? '保存中…' : '更新密码' }}
        </button>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { changePassword, updatePhone } from '../lib/api'

const props = defineProps({
  user: { type: Object, default: null }
})

const emit = defineEmits(['back', 'updated'])

const isBuiltinAdmin = computed(() => props.user?.id === 0 && props.user?.username === 'admin')

const nextPhone = ref(props.user?.phone || '')
const phonePassword = ref('')
const phoneSaving = ref(false)

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const passwordSaving = ref(false)

const message = ref('')
const messageType = ref('info')
let messageTimer = null

function setMsg(text, type = 'info') {
  message.value = text
  messageType.value = type
  if (messageTimer) clearTimeout(messageTimer)
  if (text && (type === 'success' || type === 'info')) {
    messageTimer = setTimeout(() => {
      message.value = ''
      messageType.value = 'info'
      messageTimer = null
    }, 1800)
  }
}

async function savePhone() {
  const phone = nextPhone.value.trim()
  if (!props.user?.id) return
  if (!phone) return setMsg('请输入新的手机号。', 'error')
  if (!/^\d{11}$/.test(phone)) return setMsg('手机号格式不正确，必须为 11 位数字。', 'error')
  if (!phonePassword.value) return setMsg('请输入当前密码用于验证。', 'error')
  if (phone === (props.user?.phone || '')) return setMsg('手机号未变化。', 'info')

  phoneSaving.value = true
  setMsg('')
  try {
    const data = await updatePhone({
      userId: props.user.id,
      password: phonePassword.value,
      phone,
      sessionToken: props.user.sessionToken
    })
    if (data.code === 200) {
      phonePassword.value = ''
      setMsg(data.msg || '手机号修改申请已提交。', 'success')
      return
    }
    setMsg(data.msg || '保存失败。', 'error')
  } catch (err) {
    setMsg(`保存失败：${err?.message || '未知错误'}`, 'error')
  } finally {
    phoneSaving.value = false
  }
}

async function savePassword() {
  if (!props.user?.id) return
  if (!oldPassword.value) return setMsg('请输入旧密码。', 'error')
  if (!newPassword.value) return setMsg('请输入新密码。', 'error')
  if (newPassword.value !== confirmPassword.value) return setMsg('两次输入的新密码不一致。', 'error')
  if (newPassword.value.length < 8 || newPassword.value.length > 64) return setMsg('密码长度需为 8-64 位。', 'error')
  if (!/[A-Z]/.test(newPassword.value) || !/[a-z]/.test(newPassword.value) || !/\d/.test(newPassword.value)) {
    return setMsg('密码至少包含大写字母、小写字母和数字。', 'error')
  }

  passwordSaving.value = true
  setMsg('')
  try {
    const data = await changePassword({
      userId: props.user.id,
      oldPassword: oldPassword.value,
      newPassword: newPassword.value,
      sessionToken: props.user.sessionToken
    })
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
  width: 100%;
  min-width: 0;
  overflow-x: clip;
  overscroll-behavior: contain;
  touch-action: pan-y;
}

.head {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
  min-width: 0;
}

.back {
  border: 0;
  width: 40px;
  height: 40px;
  padding: 0;
  border-radius: 50%;
  background: transparent;
  color: #183b4d;
  font-size: 28px;
  line-height: 1;
  display: inline-grid;
  place-items: center;
}

.headCopy,
.cardHead {
  min-width: 0;
}

.eyebrow,
.cardKicker {
  margin: 0;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(24, 59, 77, 0.54);
}

.title,
.cardTitle {
  margin: 8px 0 0;
  line-height: 1.04;
  letter-spacing: -0.05em;
  color: #152131;
}

.title {
  font-size: clamp(30px, 4vw, 46px);
}

.card {
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(24, 33, 47, 0.08);
  box-shadow: 0 22px 54px rgba(20, 29, 41, 0.08);
}

.notice {
  margin-top: 16px;
  padding: 14px 16px;
  border-radius: 18px;
  font-size: 14px;
  font-weight: 700;
}

.notice--success {
  background: rgba(17, 97, 73, 0.1);
  color: #116149;
}

.notice--error {
  background: rgba(154, 47, 39, 0.1);
  color: #9a2f27;
}

.notice--info {
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
}

.notice--warn {
  background: rgba(191, 133, 36, 0.1);
  color: #84581c;
}

.layout {
  margin-top: 18px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 18px;
  min-width: 0;
}

.card {
  padding: 22px;
  min-width: 0;
}

.cardTitle {
  font-size: 30px;
}

.cardDesc {
  margin: 10px 0 0;
  color: rgba(24, 33, 47, 0.6);
  font-size: 14px;
  line-height: 1.6;
}

.field {
  display: grid;
  gap: 8px;
  margin-top: 18px;
  min-width: 0;
}

.fieldLabel {
  font-size: 13px;
  font-weight: 700;
  color: rgba(24, 33, 47, 0.68);
}

.input {
  width: 100%;
  min-height: 54px;
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
  border-radius: 18px;
  border: 1px solid rgba(24, 33, 47, 0.1);
  background: rgba(255, 255, 255, 0.88);
  padding: 0 16px;
  color: #18212f;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.input:focus {
  border-color: rgba(24, 59, 77, 0.28);
  box-shadow: 0 0 0 4px rgba(24, 59, 77, 0.08);
  background: #fff;
}

.input:disabled {
  opacity: 0.7;
}

.input--file {
  padding-top: 14px;
}

.passwordGrid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin: 18px 0 16px;
  min-width: 0;
}

.btn {
  min-height: 52px;
  padding: 0 18px;
  box-sizing: border-box;
  border-radius: 18px;
  border: 0;
  font-size: 14px;
  font-weight: 800;
  transition: transform 0.16s ease, box-shadow 0.16s ease, opacity 0.16s ease;
}

.btn:disabled {
  opacity: 0.6;
}

.btn--primary {
  background: linear-gradient(135deg, #d9bb87, #b78b4a);
  color: #152131;
  box-shadow: 0 14px 28px rgba(183, 139, 74, 0.24);
}

.btn--primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 18px 32px rgba(183, 139, 74, 0.3);
}

.btn--ghost {
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
}

.btn--submit {
  margin-top: 16px;
}

@media (max-width: 900px) {
  .passwordGrid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .page {
    padding: 24px 14px 120px;
  }

  .head {
    align-items: center;
  }

  .card {
    padding: 18px;
    border-radius: 24px;
  }
}
</style>
