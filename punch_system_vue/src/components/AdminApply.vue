<template>
  <div class="admin-apply">
    <div class="admin-apply__container">
      <div class="admin-apply__header">
        <h1 class="admin-apply__title">申请管理员权限</h1>
        <p class="admin-apply__subtitle">填写申请信息，等待超级管理员审批</p>
      </div>

      <div class="admin-apply__content">
        <div v-if="!hasApplied" class="apply-form">
          <div class="form-group">
            <label class="form-label">申请人</label>
            <input 
              v-model="username" 
              type="text" 
              class="form-input" 
              disabled
              placeholder="您的用户名"
            />
          </div>

          <div class="form-group">
            <label class="form-label">申请理由 <span class="required">*</span></label>
            <textarea 
              v-model="reason" 
              class="form-textarea" 
              placeholder="请详细说明您申请管理员权限的理由..."
              rows="6"
              maxlength="500"
            ></textarea>
            <p class="form-hint">{{ reason.length }}/500</p>
          </div>

          <div class="form-actions">
            <button 
              class="btn btn--primary" 
              type="button" 
              :disabled="loading || !reason.trim()"
              @click="submitApplication"
            >
              {{ loading ? '提交中...' : '提交申请' }}
            </button>
            <button 
              class="btn btn--ghost" 
              type="button" 
              @click="$emit('cancel')"
            >
              取消
            </button>
          </div>
        </div>

        <div v-else class="applied-status">
          <div class="status-card">
            <div class="status-icon">📋</div>
            <h3 class="status-title">申请已提交</h3>
            <p class="status-text">您的管理员申请已提交，请等待超级管理员审批。</p>
            <p class="status-time">提交时间：{{ applicationTime }}</p>
          </div>
        </div>

        <div v-if="message" class="message" :class="`message--${messageType}`">
          {{ message }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { applyForAdmin } from '../lib/api'

const props = defineProps({
  user: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['cancel', 'success'])

const username = ref(props.user.username)
const reason = ref('')
const loading = ref(false)
const message = ref('')
const messageType = ref('info')
const hasApplied = ref(false)
const applicationTime = ref('')

async function submitApplication() {
  if (!reason.value.trim()) {
    message.value = '请填写申请理由'
    messageType.value = 'error'
    return
  }

  loading.value = true
  message.value = ''
  
  try {
    const data = await applyForAdmin({
      user_id: props.user.id,
      username: props.user.username,
      reason: reason.value.trim()
    })
    
    if (data.code === 200) {
      message.value = data.msg
      messageType.value = 'success'
      hasApplied.value = true
      applicationTime.value = new Date().toLocaleString('zh-CN')
      
      setTimeout(() => {
        emit('success')
      }, 2000)
    } else {
      message.value = data.msg
      messageType.value = 'error'
    }
  } catch (err) {
    message.value = `申请失败：${err?.message || '未知错误'}`
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.admin-apply {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.admin-apply__container {
  width: 100%;
  max-width: 600px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(20px);
  padding: 40px;
}

.admin-apply__header {
  text-align: center;
  margin-bottom: 32px;
}

.admin-apply__title {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 12px;
}

.admin-apply__subtitle {
  font-size: 16px;
  color: #64748b;
  margin: 0;
}

.admin-apply__content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.apply-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.required {
  color: #ef4444;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  font-family: inherit;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-input:disabled {
  background: #f8fafc;
  color: #64748b;
  cursor: not-allowed;
}

.form-textarea {
  resize: vertical;
  min-height: 120px;
}

.form-hint {
  font-size: 12px;
  color: #94a3b8;
  text-align: right;
  margin: 4px 0 0;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn--primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn--primary:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn--ghost {
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid #e2e8f0;
  color: #64748b;
}

.btn--ghost:hover:not(:disabled) {
  border-color: #667eea;
  color: #667eea;
}

.applied-status {
  display: flex;
  justify-content: center;
}

.status-card {
  text-align: center;
  padding: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
}

.status-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.status-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 12px;
}

.status-text {
  font-size: 16px;
  opacity: 0.9;
  margin: 0 0 8px;
}

.status-time {
  font-size: 14px;
  opacity: 0.7;
  margin: 0;
}

.message {
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  text-align: center;
}

.message--success {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #86efac;
}

.message--error {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}

.message--info {
  background: #dbeafe;
  color: #1e40af;
  border: 1px solid #93c5fd;
}

@media (max-width: 768px) {
  .admin-apply__container {
    padding: 24px;
  }

  .admin-apply__title {
    font-size: 24px;
  }

  .form-actions {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }
}
</style>