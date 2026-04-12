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
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(24, 33, 47, 0.08);
  border-radius: 28px;
  box-shadow: 0 24px 64px rgba(20, 29, 41, 0.12);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  padding: 28px 24px;
  text-align: left;
  position: relative;
  overflow: hidden;
}

.card::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 12% 14%, rgba(215, 177, 120, 0.26), transparent 26%),
    radial-gradient(circle at 86% 12%, rgba(109, 139, 116, 0.18), transparent 24%);
  opacity: 0.95;
}

.card__head {
  margin-bottom: 18px;
  position: relative;
  z-index: 1;
}

.card__title {
  margin: 0;
  font-size: 28px;
  letter-spacing: -0.03em;
  color: #152131;
}

.card__sub {
  margin: 8px 0 0;
  color: rgba(24, 33, 47, 0.58);
  font-size: 14px;
}

.form {
  display: grid;
  gap: 14px;
  position: relative;
  z-index: 1;
}

.field {
  display: grid;
  gap: 8px;
}

.field__label {
  font-size: 13px;
  font-weight: 700;
  color: rgba(24, 33, 47, 0.66);
}

.field__input {
  min-height: 54px;
  padding: 0 14px;
  border: 1px solid rgba(24, 33, 47, 0.1);
  border-radius: 16px;
  outline: none;
  background: rgba(255, 255, 255, 0.92);
  color: #18212f;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.field__input:focus {
  border-color: rgba(24, 59, 77, 0.3);
  box-shadow: 0 0 0 4px rgba(24, 59, 77, 0.08);
}

.row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.link {
  border: 0;
  background: transparent;
  color: #183b4d;
  font-weight: 700;
  padding: 6px 0;
  transition: transform 0.16s ease, opacity 0.16s ease;
}

.link:hover {
  transform: translateY(-1px);
  opacity: 0.76;
}

.link:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn {
  width: 100%;
  min-height: 56px;
  border: 0;
  border-radius: 16px;
  padding: 0 14px;
  background: linear-gradient(135deg, #d9bb87, #b78b4a);
  color: #fffaf0;
  font-weight: 800;
  box-shadow: 0 14px 30px rgba(183, 139, 74, 0.22);
  transition: transform 0.16s ease, box-shadow 0.16s ease, opacity 0.16s ease;
}

.btn:hover:not(:disabled) {
  box-shadow: 0 18px 34px rgba(183, 139, 74, 0.28);
  transform: translateY(-1px);
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.alert {
  border-radius: 16px;
  padding: 12px 14px;
  font-size: 13px;
  font-weight: 700;
}

.alert--success {
  background: rgba(17, 97, 73, 0.1);
  color: #116149;
}

.alert--error {
  background: rgba(154, 47, 39, 0.1);
  color: #9a2f27;
}

.alert--warn {
  background: rgba(132, 88, 28, 0.1);
  color: #84581c;
}

.alert--info {
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
}

@media (max-width: 640px) {
  .auth {
    padding: 24px 14px;
  }

  .card {
    border-radius: 24px;
    padding: 24px 18px;
  }

  .card__title {
    font-size: 24px;
  }
}
</style>
