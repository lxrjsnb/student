<template>
  <section class="shell">
    <div class="card">
      <div class="head">
        <h2 class="title">
          <template v-if="mode === 'login'">
            <span class="title-main">迹刻</span>
            <span class="title-sub">- 即刻打卡</span>
          </template>
          <template v-else>
            <span class="title-main">注册账号</span>
          </template>
        </h2>
        <p class="subtitle">{{ mode === 'login' ? '请输入账号和密码继续使用' : '创建一个基础账号后进入系统' }}</p>
      </div>

      <form class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span>账号</span>
          <input
            v-model.trim="username"
            type="text"
            autocomplete="username"
            placeholder="请输入账号"
            :disabled="loading"
            required
          />
        </label>

      <label class="field">
        <span>密码</span>
        <input
          v-model="password"
            type="password"
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
            placeholder="请输入密码"
          :disabled="loading"
          required
        />
      </label>

      <p v-if="inlineLoginError" class="inline-error">{{ inlineLoginError }}</p>

      <label v-if="mode === 'register'" class="field">
        <span>确认密码</span>
        <input
            v-model="confirmPassword"
            type="password"
            autocomplete="new-password"
            placeholder="再次输入密码"
            :disabled="loading"
            required
          />
        </label>

      <button class="submit" type="submit" :disabled="loading">
        {{ loading ? '处理中...' : mode === 'login' ? '登录' : '注册' }}
      </button>

      <div v-if="showBottomAlert" class="alert" :class="`alert--${messageType}`">
        {{ message }}
      </div>
    </form>

      <p class="switch-row">
        {{ mode === 'login' ? '还没有账号？' : '已有账号？' }}
        <a href="#" @click.prevent="$emit('switchMode', mode === 'login' ? 'register' : 'login')">
          {{ mode === 'login' ? '去注册' : '去登录' }}
        </a>
      </p>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  mode: { type: String, required: true },
  loading: { type: Boolean, default: false },
  message: { type: String, default: '' },
  messageType: { type: String, default: 'info' },
  apiBaseUrl: { type: String, required: true },
  defaultUsername: { type: String, default: '' }
})

const emit = defineEmits(['auth', 'switchMode', 'goAdmin'])

const username = ref(props.defaultUsername)
const password = ref('')
const confirmPassword = ref('')

const inlineLoginError = computed(() => {
  if (props.mode !== 'login') return ''
  if (props.messageType !== 'error') return ''
  return '账号或密码错误'
})

const showBottomAlert = computed(() => {
  if (!props.message) return false
  return !inlineLoginError.value
})

function onSubmit() {
  emit('auth', {
    mode: props.mode,
    username: username.value,
    password: password.value,
    confirmPassword: confirmPassword.value,
    remember: true
  })
}
</script>

<style scoped>
.shell {
  width: min(420px, 100%);
}

.card {
  border-radius: 30px;
  border: 1px solid rgba(24, 33, 47, 0.08);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow: 0 24px 64px rgba(20, 29, 41, 0.12);
}

.card {
  width: 100%;
  padding: 30px 26px;
  background: rgba(255, 255, 255, 0.82);
}

.head {
  margin-bottom: 22px;
}

.title {
  margin: 0;
  display: flex;
  align-items: flex-end;
  gap: 10px;
  flex-wrap: wrap;
  line-height: 1;
  color: #152131;
}

.title-main {
  font-size: 34px;
  letter-spacing: -0.05em;
}

.title-sub {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: rgba(24, 33, 47, 0.58);
  padding-bottom: 4px;
}

.subtitle {
  margin: 10px 0 0;
  font-size: 14px;
  color: rgba(24, 33, 47, 0.58);
}

.form {
  display: grid;
  gap: 14px;
}

.field {
  display: grid;
  gap: 8px;
}

.field span {
  font-size: 13px;
  font-weight: 700;
  color: rgba(24, 33, 47, 0.66);
}

.field input {
  min-height: 54px;
  border-radius: 16px;
  border: 1px solid rgba(24, 33, 47, 0.1);
  background: rgba(255, 255, 255, 0.92);
  padding: 0 14px;
  font-size: 15px;
  color: #18212f;
  outline: none;
}

.field input:focus {
  border-color: rgba(24, 59, 77, 0.3);
  box-shadow: 0 0 0 4px rgba(24, 59, 77, 0.08);
}

.inline-error {
  margin: -4px 0 0;
  font-size: 13px;
  font-weight: 700;
  color: #9a2f27;
}

.submit {
  min-height: 56px;
  border: 0;
  border-radius: 16px;
  background: linear-gradient(135deg, #183b4d, #29546c);
  color: #f8f4ec;
  font-size: 15px;
  font-weight: 800;
}

.submit:disabled {
  opacity: 0.66;
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

.switch-row {
  margin: 18px 0 0;
  font-size: 14px;
  color: rgba(24, 33, 47, 0.58);
}

.switch-row a {
  color: #183b4d;
  font-weight: 800;
  text-decoration: none;
  margin-left: 6px;
}

@media (max-width: 640px) {
  .card {
    padding: 24px 18px;
    border-radius: 24px;
  }

  .title {
    gap: 8px;
  }

  .title-main {
    font-size: 28px;
  }

  .title-sub {
    font-size: 13px;
  }
}
</style>
