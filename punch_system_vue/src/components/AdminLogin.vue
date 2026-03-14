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
  background: rgba(10, 25, 47, 0.85);
  border: 1px solid rgba(66, 153, 225, 0.3);
  border-radius: 16px;
  box-shadow: 0 0 30px rgba(66, 153, 225, 0.2);
  backdrop-filter: blur(12px);
  padding: 22px;
  text-align: left;
  position: relative;
  overflow: hidden;
}

.card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #4299e1, transparent);
  animation: borderGlow 3s ease-in-out infinite;
}

@keyframes borderGlow {
  0%, 100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

.card__head {
  margin-bottom: 16px;
}

.card__title {
  margin: 0;
  font-size: 22px;
  letter-spacing: 0.2px;
  color: #e2e8f0;
  text-align: center;
}

.card__sub {
  margin: 6px 0 0;
  color: #94a3b8;
  font-size: 13px;
  text-align: center;
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
  color: #94a3b8;
}

.field__input {
  padding: 12px 12px;
  border: 1px solid rgba(66, 153, 225, 0.3);
  border-radius: 12px;
  outline: none;
  background: rgba(15, 30, 50, 0.8);
  color: #e2e8f0;
  transition: all 0.3s ease;
}

.field__input:focus {
  border-color: #4299e1;
  box-shadow: 0 0 0 4px rgba(66, 153, 225, 0.15);
  background: rgba(15, 30, 50, 1);
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
  color: #4299e1;
  font-weight: 700;
  padding: 6px 0;
  transition: transform 0.16s ease, filter 0.16s ease;
}

.link:hover {
  transform: translateY(-1px);
  filter: saturate(1.1);
  color: #63b3ed;
}

.link:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn {
  width: 100%;
  border: 1px solid rgba(66, 153, 225, 0.5);
  border-radius: 12px;
  padding: 12px 14px;
  background: linear-gradient(135deg, rgba(66, 153, 225, 0.2), rgba(66, 153, 225, 0.4));
  background-size: 200% 200%;
  animation: bgShift 10s ease-in-out infinite;
  color: #e2e8f0;
  font-weight: 800;
  transition: all 0.3s ease;
}

.btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(66, 153, 225, 0.3), rgba(66, 153, 225, 0.6));
  box-shadow: 0 0 20px rgba(66, 153, 225, 0.3);
  transform: translateY(-1px);
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
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.3);
}

.alert--error {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.3);
}

.alert--warn {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
  border-color: rgba(245, 158, 11, 0.3);
}

.alert--info {
  background: rgba(66, 153, 225, 0.1);
  color: #4299e1;
  border-color: rgba(66, 153, 225, 0.3);
}
</style>
