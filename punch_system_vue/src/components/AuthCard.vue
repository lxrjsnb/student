<template>
  <div class="login-card">
    <div class="login-header">
      <div class="logo" aria-hidden="true">🌿</div>
      <h1>DakaLa | 打卡啦</h1>
      <p class="subtitle">{{ mode === 'login' ? '简单打卡，美好生活' : '创建账号，开启打卡' }}</p>
    </div>

    <form class="login-form" @submit.prevent="onSubmit">
      <div class="input-group">
        <span class="icon" aria-hidden="true">👤</span>
        <input
          v-model.trim="username"
          type="text"
          autocomplete="username"
          placeholder="用户名 / 邮箱 / 手机号"
          :disabled="loading"
          required
        />
      </div>

      <div class="input-group">
        <span class="icon" aria-hidden="true">🔒</span>
        <input
          v-model="password"
          type="password"
          :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
          placeholder="密码"
          :disabled="loading"
          required
        />
      </div>

      <div v-if="mode === 'register'" class="input-group">
        <span class="icon" aria-hidden="true">🔒</span>
        <input
          v-model="confirmPassword"
          type="password"
          autocomplete="new-password"
          placeholder="确认密码"
          :disabled="loading"
          required
        />
      </div>

      <div class="form-actions">
        <label class="remember-me">
          <input v-model="remember" type="checkbox" :disabled="loading" />
          <span>记住我</span>
        </label>
        <a class="forgot-pwd" href="#" @click.prevent>忘记密码？</a>
      </div>

      <button class="submit-btn" type="submit" :disabled="loading">
        {{ loading ? '处理中...' : mode === 'login' ? '登 录' : '注 册' }}
      </button>

      <div v-if="message" class="alert" :class="`alert--${messageType}`">
        {{ message }}
      </div>
    </form>

    <div class="login-footer">
      <div class="divider">
        <span>或通过以下方式登录</span>
      </div>
      <div class="third-party">
        <button class="icon-btn wechat" type="button" disabled title="未实现">💬</button>
        <button class="icon-btn google" type="button" disabled title="未实现">G</button>
      </div>

      <p class="register-hint">
        {{ mode === 'login' ? '还没有账号？' : '已有账号？' }}
        <a
          class="register-link"
          href="#"
          @click.prevent="$emit('switchMode', mode === 'login' ? 'register' : 'login')"
        >
          {{ mode === 'login' ? '立即注册' : '去登录' }}
        </a>
      </p>

      <p class="hint">
        <span class="hint__k">接口地址：</span>
        <span class="hint__v">{{ apiBaseUrl }}</span>
      </p>
    </div>
  </div>
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

const emit = defineEmits(['auth', 'switchMode', 'goAdmin'])

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
.alert {
  margin-top: 12px;
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 13px;
  border: 1px solid transparent;
}

.alert--success {
  background: rgba(34, 197, 94, 0.12);
  color: #15803d;
  border-color: rgba(34, 197, 94, 0.25);
}

.alert--error {
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
  border-color: rgba(239, 68, 68, 0.25);
}

.alert--warn {
  background: rgba(245, 158, 11, 0.12);
  color: #b45309;
  border-color: rgba(245, 158, 11, 0.25);
}

.alert--info {
  background: rgba(0, 168, 204, 0.12);
  color: #008ba8;
  border-color: rgba(0, 168, 204, 0.25);
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 40px 30px;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.login-header .logo {
  font-size: 40px;
  margin-bottom: 10px;
}

.login-header h1 {
  font-size: 24px;
  color: #333;
  margin: 0 0 5px 0;
  font-weight: 600;
}

.login-header .subtitle {
  font-size: 14px;
  color: #666;
  margin-bottom: 30px;
}

.login-form {
  display: grid;
}

.input-group {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 10px;
  padding: 0 15px;
  margin-bottom: 15px;
  border: 1px solid transparent;
  transition: border-color 0.3s ease;
}

.input-group:focus-within {
  border-color: #00a8cc;
}

.input-group .icon {
  font-size: 18px;
  color: #888;
  margin-right: 10px;
}

.input-group input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 12px 0;
  font-size: 15px;
  color: #333;
  outline: none;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  margin-bottom: 25px;
  padding: 0 5px;
}

.remember-me {
  display: flex;
  align-items: center;
  color: #555;
  cursor: pointer;
}

.remember-me input {
  margin-right: 5px;
}

.forgot-pwd {
  color: #00a8cc;
  text-decoration: none;
}

.forgot-pwd:hover {
  text-decoration: underline;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background: #00a8cc;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 168, 204, 0.3);
}

.submit-btn:hover {
  background: #008ba8;
  transform: translateY(-2px);
}

.submit-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.login-footer {
  margin-top: 30px;
}

.divider {
  position: relative;
  text-align: center;
  margin-bottom: 20px;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: rgba(0, 0, 0, 0.1);
  z-index: 1;
}

.divider span {
  position: relative;
  z-index: 2;
  background: rgba(255, 255, 255, 0.1);
  padding: 0 10px;
  font-size: 12px;
  color: #888;
}

.third-party {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-bottom: 20px;
}

.icon-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: white;
  cursor: pointer;
  font-size: 18px;
  transition: transform 0.2s;
}

.icon-btn:hover:not(:disabled) {
  transform: scale(1.1);
}

.icon-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.wechat {
  color: #07c160;
}

.google {
  color: #ea4335;
  font-weight: bold;
}

.register-hint {
  font-size: 14px;
  color: #666;
}

.register-link {
  color: #00a8cc;
  text-decoration: none;
  font-weight: 500;
}

.register-link:hover {
  text-decoration: underline;
}

.hint {
  font-size: 12px;
  color: #888;
  margin-top: 10px;
  word-break: break-all;
}

.hint__k {
  color: #888;
}
</style>
