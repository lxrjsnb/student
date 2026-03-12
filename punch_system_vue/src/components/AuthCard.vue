<template>
  <section class="auth">
    <div class="card">
      <div class="card__head">
        <h1 class="card__title">{{ mode === 'login' ? '登录' : '注册' }}</h1>
        <p class="card__sub">
          {{ mode === 'login' ? '使用账号密码进入打卡系统。' : '创建账号后即可打卡。' }}
        </p>
      </div>

      <form class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span class="field__label">用户名</span>
          <input
            v-model.trim="username"
            class="field__input"
            autocomplete="username"
            placeholder="例如：test"
            :disabled="loading"
            required
          />
        </label>

        <label class="field">
          <span class="field__label">密码</span>
          <input
            v-model="password"
            class="field__input"
            type="password"
            autocomplete="current-password"
            placeholder="请输入密码"
            :disabled="loading"
            required
          />
        </label>

        <label v-if="mode === 'register'" class="field">
          <span class="field__label">确认密码</span>
          <input
            v-model="confirmPassword"
            class="field__input"
            type="password"
            autocomplete="new-password"
            placeholder="再次输入密码"
            :disabled="loading"
            required
          />
        </label>

        <div class="row">
          <label class="check">
            <input v-model="remember" type="checkbox" :disabled="loading" />
            <span>记住登录</span>
          </label>

          <button
            class="link"
            type="button"
            :disabled="loading"
            @click="$emit('switchMode', mode === 'login' ? 'register' : 'login')"
          >
            {{ mode === 'login' ? '没有账号？去注册' : '已有账号？去登录' }}
          </button>
        </div>

        <button class="btn" type="submit" :disabled="loading">
          {{ loading ? '处理中…' : mode === 'login' ? '登录' : '注册' }}
        </button>

        <div v-if="message" class="alert" :class="`alert--${messageType}`">
          {{ message }}
        </div>

        <div class="hint">
          <span class="hint__k">接口地址：</span>
          <span class="hint__v">{{ apiBaseUrl }}</span>
        </div>
      </form>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  mode: { type: String, required: true }, // login | register
  loading: { type: Boolean, default: false },
  message: { type: String, default: '' },
  messageType: { type: String, default: 'info' }, // info | success | error | warn
  apiBaseUrl: { type: String, required: true },
  defaultUsername: { type: String, default: '' }
})

const emit = defineEmits(['auth', 'switchMode'])

const username = ref(props.defaultUsername)
const password = ref('')
const confirmPassword = ref('')
const remember = ref(true)

function onSubmit() {
  emit('auth', {
    mode: props.mode,
    username: username.value,
    password: password.value,
    confirmPassword: confirmPassword.value,
    remember: remember.value
  })
}
</script>

<style scoped>
.auth {
  display: grid;
  place-items: center;
  padding: 40px 20px;
}

.card {
  width: 100%;
  max-width: 420px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(229, 231, 235, 0.9);
  border-radius: 16px;
  box-shadow: var(--shadow-strong);
  backdrop-filter: blur(12px);
  padding: 22px;
  text-align: left;
}

.card__head {
  margin-bottom: 16px;
}

.card__title {
  margin: 0;
  font-size: 22px;
  letter-spacing: 0.2px;
}

.card__sub {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: 13px;
}

.form {
  display: grid;
  gap: 12px;
}

.field {
  display: grid;
  gap: 8px;
}

.field__label {
  font-size: 13px;
  color: var(--muted);
}

.field__input {
  padding: 12px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  outline: none;
  background: #fff;
}

.field__input:focus {
  border-color: rgba(37, 99, 235, 0.55);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 13px;
}

.link {
  border: 0;
  background: transparent;
  color: var(--primary);
  font-weight: 700;
  padding: 6px 0;
  transition: transform 0.16s ease, filter 0.16s ease;
}

.link:hover {
  transform: translateY(-1px);
  filter: saturate(1.1);
}

.link:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn {
  width: 100%;
  border: 1px solid transparent;
  border-radius: 12px;
  padding: 12px 14px;
  background: linear-gradient(135deg, var(--primary), var(--accent), var(--accent2));
  background-size: 200% 200%;
  animation: bgShift 10s ease-in-out infinite;
  color: var(--primary-ink);
  font-weight: 800;
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.alert {
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 13px;
  border: 1px solid transparent;
}

.alert--success {
  background: var(--success-bg);
  color: var(--success-ink);
  border-color: rgba(6, 95, 70, 0.2);
}

.alert--error {
  background: var(--danger-bg);
  color: var(--danger-ink);
  border-color: rgba(153, 27, 27, 0.2);
}

.alert--warn {
  background: var(--warn-bg);
  color: var(--warn-ink);
  border-color: rgba(146, 64, 14, 0.2);
}

.alert--info {
  background: #eff6ff;
  color: #1e40af;
  border-color: rgba(30, 64, 175, 0.2);
}

.hint {
  display: flex;
  gap: 6px;
  font-size: 12px;
  color: var(--muted);
  margin-top: 6px;
  word-break: break-all;
}

.hint__k {
  color: #94a3b8;
}
</style>
