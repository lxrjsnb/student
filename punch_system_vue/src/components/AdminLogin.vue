<template>
  <section class="auth">
    <div class="card">
      <div class="card__head">
        <h1 class="card__title">管理员登录</h1>
        <p class="card__sub">仅限授权管理员访问。</p>
      </div>

      <form class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span class="field__label">管理员账号</span>
          <input
            v-model.trim="username"
            class="field__input"
            autocomplete="username"
            placeholder="请输入管理员账号"
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

        <div class="row">
          <button class="link" type="button" :disabled="loading" @click="$emit('goHome')">
            返回普通用户登录
          </button>
        </div>

        <button class="btn" type="submit" :disabled="loading">
          {{ loading ? '登录中…' : '登录' }}
        </button>

        <div v-if="message" class="alert" :class="`alert--${messageType}`">
          {{ message }}
        </div>
      </form>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  loading: { type: Boolean, default: false },
  message: { type: String, default: '' },
  messageType: { type: String, default: 'info' }
})

const emit = defineEmits(['login', 'goHome'])

const username = ref('')
const password = ref('')

function onSubmit() {
  emit('login', {
    username: username.value,
    password: password.value
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
  justify-content: flex-end;
  gap: 12px;
  flex-wrap: wrap;
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
</style>
