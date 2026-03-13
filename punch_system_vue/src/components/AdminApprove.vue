<template>
  <div class="admin-approve">
    <div class="admin-approve__container">
      <div class="admin-approve__header">
        <div>
          <h1 class="admin-approve__title">管理员申请审批</h1>
          <p class="admin-approve__subtitle">审核用户的管理员申请</p>
        </div>
        <button class="btn btn--ghost" type="button" @click="loadApplications">
          {{ loading ? '加载中...' : '🔄 刷新' }}
        </button>
      </div>

      <div class="admin-approve__content">
        <div v-if="applications.length === 0 && !loading" class="empty-state">
          <div class="empty-icon">📭</div>
          <h3 class="empty-title">暂无申请</h3>
          <p class="empty-text">目前没有待审批的管理员申请</p>
        </div>

        <div v-else class="applications-list">
          <div 
            v-for="application in applications" 
            :key="application.id" 
            class="application-card"
            :class="`application-card--${application.status}`"
          >
            <div class="application-header">
              <div class="applicant-info">
                <div class="applicant-avatar">
                  {{ application.username.charAt(0).toUpperCase() }}
                </div>
                <div class="applicant-details">
                  <h4 class="applicant-name">{{ application.username }}</h4>
                  <p class="applicant-id">ID: {{ application.user_id }}</p>
                </div>
              </div>
              <div class="application-status">
                <span 
                  class="status-badge" 
                  :class="`status-badge--${application.status}`"
                >
                  {{ getStatusText(application.status) }}
                </span>
              </div>
            </div>

            <div class="application-body">
              <div class="reason-section">
                <h5 class="reason-label">申请理由</h5>
                <p class="reason-text">{{ application.reason }}</p>
              </div>

              <div class="application-meta">
                <div class="meta-item">
                  <span class="meta-icon">📅</span>
                  <span class="meta-text">申请时间：{{ formatDate(application.created_at) }}</span>
                </div>
              </div>
            </div>

            <div v-if="application.status === 'pending'" class="application-actions">
              <button 
                class="btn btn--success" 
                type="button" 
                :disabled="processing"
                @click="approveApplication(application.id)"
              >
                ✓ 批准
              </button>
              <button 
                class="btn btn--danger" 
                type="button" 
                :disabled="processing"
                @click="rejectApplication(application.id)"
              >
                ✕ 拒绝
              </button>
            </div>
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
import { ref, onMounted } from 'vue'
import { getAdminApplications, approveAdminApplication } from '../lib/api'

const applications = ref([])
const loading = ref(false)
const processing = ref(false)
const message = ref('')
const messageType = ref('info')

async function loadApplications() {
  loading.value = true
  message.value = ''
  
  try {
    const data = await getAdminApplications()
    if (data.code === 200) {
      applications.value = data.data || []
    } else {
      message.value = data.msg || '加载失败'
      messageType.value = 'error'
    }
  } catch (err) {
    message.value = `加载失败：${err?.message || '未知错误'}`
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}

async function approveApplication(applicationId) {
  if (!confirm('确定要批准此申请吗？')) return
  
  processing.value = true
  message.value = ''
  
  try {
    const data = await approveAdminApplication({
      application_id: applicationId,
      action: 'approve'
    })
    
    if (data.code === 200) {
      message.value = data.msg
      messageType.value = 'success'
      await loadApplications()
    } else {
      message.value = data.msg || '操作失败'
      messageType.value = 'error'
    }
  } catch (err) {
    message.value = `操作失败：${err?.message || '未知错误'}`
    messageType.value = 'error'
  } finally {
    processing.value = false
  }
}

async function rejectApplication(applicationId) {
  if (!confirm('确定要拒绝此申请吗？')) return
  
  processing.value = true
  message.value = ''
  
  try {
    const data = await approveAdminApplication({
      application_id: applicationId,
      action: 'reject'
    })
    
    if (data.code === 200) {
      message.value = data.msg
      messageType.value = 'success'
      await loadApplications()
    } else {
      message.value = data.msg || '操作失败'
      messageType.value = 'error'
    }
  } catch (err) {
    message.value = `操作失败：${err?.message || '未知错误'}`
    messageType.value = 'error'
  } finally {
    processing.value = false
  }
}

function getStatusText(status) {
  const statusMap = {
    'pending': '待审批',
    'approved': '已批准',
    'rejected': '已拒绝'
  }
  return statusMap[status] || status
}

function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadApplications()
})
</script>

<style scoped>
.admin-approve {
  min-height: 100vh;
  padding: 24px;
}

.admin-approve__container {
  max-width: 1200px;
  margin: 0 auto;
}

.admin-approve__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  gap: 20px;
}

.admin-approve__title {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px;
}

.admin-approve__subtitle {
  font-size: 16px;
  color: #64748b;
  margin: 0;
}

.admin-approve__content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px;
}

.empty-text {
  font-size: 16px;
  color: #64748b;
  margin: 0;
}

.applications-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.application-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: transform 0.3s ease;
}

.application-card:hover {
  transform: translateY(-4px);
}

.application-card--approved {
  border-left: 4px solid #22c55e;
}

.application-card--rejected {
  border-left: 4px solid #ef4444;
}

.application-card--pending {
  border-left: 4px solid #f59e0b;
}

.application-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.applicant-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.applicant-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
}

.applicant-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.applicant-name {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.applicant-id {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.application-status {
  display: flex;
  align-items: center;
}

.status-badge {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}

.status-badge--pending {
  background: #fef3c7;
  color: #92400e;
}

.status-badge--approved {
  background: #dcfce7;
  color: #166534;
}

.status-badge--rejected {
  background: #fee2e2;
  color: #991b1b;
}

.application-body {
  padding: 20px;
}

.reason-section {
  margin-bottom: 16px;
}

.reason-label {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px;
}

.reason-text {
  font-size: 15px;
  color: #475569;
  line-height: 1.6;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.application-meta {
  display: flex;
  gap: 20px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-icon {
  font-size: 16px;
}

.meta-text {
  font-size: 14px;
  color: #64748b;
}

.application-actions {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
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

.btn--ghost {
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid #e2e8f0;
  color: #64748b;
}

.btn--ghost:hover:not(:disabled) {
  border-color: #667eea;
  color: #667eea;
}

.btn--success {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  color: white;
}

.btn--success:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(34, 197, 94, 0.4);
}

.btn--danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.btn--danger:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
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
  .admin-approve__header {
    flex-direction: column;
    align-items: flex-start;
  }

  .application-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .application-actions {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }
}
</style>