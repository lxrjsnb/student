<template>
  <div class="super-admin-dashboard">
    <div class="dashboard-bg" aria-hidden="true"></div>
    <div class="dashboard">
      <div class="dashboard__header">
        <div class="header-content">
          <div class="header-icon">{{ isSuperAdmin ? '👑' : '👨‍💼' }}</div>
          <div class="header-text">
            <h1 class="dashboard__title">{{ isSuperAdmin ? '超级管理员控制台' : '管理员控制台' }}</h1>
            <p class="dashboard__subtitle">{{ isSuperAdmin ? '管理系统与审批申请' : '管理系统数据' }}</p>
          </div>
        </div>
        <button class="btn btn--ghost" type="button" @click="$emit('logout')">
          退出登录
        </button>
      </div>

      <div class="dashboard__content">
        <div class="dashboard__section">
          <h2 class="section-title">📊 数据管理</h2>
          <div class="mini-app-grid">
            <div class="mini-app-card" @click="$emit('goUsers')">
              <div class="mini-app-icon">👥</div>
              <div class="mini-app-title">用户管理</div>
              <div class="mini-app-desc">查看和修改用户信息</div>
            </div>
            <div class="mini-app-card" @click="$emit('goRecords')">
              <div class="mini-app-icon">📋</div>
              <div class="mini-app-title">打卡记录</div>
              <div class="mini-app-desc">查看所有打卡记录</div>
            </div>
            <div class="mini-app-card" @click="$emit('goOverview')">
              <div class="mini-app-icon">📰</div>
              <div class="mini-app-title">内容管理</div>
              <div class="mini-app-desc">编辑公告和图片</div>
            </div>
          </div>
        </div>

        <div v-if="isSuperAdmin" class="dashboard__section">
          <h2 class="section-title">✍️ 权限管理</h2>
          <div class="mini-app-grid">
            <div class="mini-app-card mini-app-card--highlight" @click="$emit('goApprove')">
              <div class="mini-app-icon">🔐</div>
              <div class="mini-app-title">审批申请</div>
              <div class="mini-app-desc">审批管理员申请</div>
              <div v-if="pendingCount > 0" class="mini-app-badge">{{ pendingCount }}</div>
            </div>
            <div class="mini-app-card" @click="$emit('goAdmins')">
              <div class="mini-app-icon">👨‍💼</div>
              <div class="mini-app-title">管理员列表</div>
              <div class="mini-app-desc">查看所有管理员</div>
            </div>
          </div>
        </div>

        <div class="dashboard__section">
          <h2 class="section-title">📈 系统统计</h2>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ stats.totalUsers }}</div>
              <div class="stat-label">总用户数</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ stats.totalAdmins }}</div>
              <div class="stat-label">管理员数</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ stats.totalRecords }}</div>
              <div class="stat-label">打卡总数</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ stats.pendingApps }}</div>
              <div class="stat-label">待审批</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAllUsers, getAllRecords, getAdminApplications } from '../lib/api'

const props = defineProps({
  isSuperAdmin: {
    type: Boolean,
    default: false
  },
  token: {
    type: String,
    required: true
  },
  role: {
    type: String,
    default: 'user'
  }
})

const emit = defineEmits(['logout', 'goUsers', 'goRecords', 'goOverview', 'goApprove', 'goAdmins'])

const stats = ref({
  totalUsers: 0,
  totalAdmins: 0,
  totalRecords: 0,
  pendingApps: 0
})

const pendingCount = ref(0)

async function loadStats() {
  try {
    const [usersRes, recordsRes] = await Promise.all([
      getAllUsers({ token: props.token, role: props.role }),
      getAllRecords({ token: props.token, role: props.role })
    ])

    if (usersRes.code === 200) {
      stats.value.totalUsers = usersRes.data.length
      stats.value.totalAdmins = usersRes.data.filter(u => u.role === 'admin' || u.role === 'super_admin').length
    }

    if (recordsRes.code === 200) {
      stats.value.totalRecords = recordsRes.data.length
    }

    try {
      const appsRes = await getAdminApplications({ token: props.token, role: props.role })
      if (appsRes.code === 200) {
        const pendingApps = appsRes.data.filter(app => app.status === 'pending')
        stats.value.pendingApps = pendingApps.length
        pendingCount.value = pendingApps.length
      }
    } catch (err) {
      console.warn('无法加载申请列表（可能是数据库表未创建）:', err.message)
      stats.value.pendingApps = 0
      pendingCount.value = 0
    }
  } catch (err) {
    console.error('加载统计数据失败:', err)
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.super-admin-dashboard {
  min-height: 100vh;
  position: relative;
}

.dashboard-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  z-index: -1;
  animation: bgShift 20s ease infinite;
}

@keyframes bgShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.dashboard {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.dashboard__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(20px);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dashboard__title {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.dashboard__subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.dashboard__content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.dashboard__section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(20px);
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 20px;
}

.mini-app-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.mini-app-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 12px;
  border: 2px solid transparent;
  position: relative;
}

.mini-app-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.2);
  border-color: #667eea;
}

.mini-app-card--highlight {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.mini-app-card--highlight:hover {
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.4);
}

.mini-app-icon {
  font-size: 48px;
  line-height: 1;
}

.mini-app-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.mini-app-card--highlight .mini-app-title {
  color: white;
}

.mini-app-desc {
  font-size: 12px;
  color: #64748b;
  margin: 0;
  line-height: 1.4;
}

.mini-app-card--highlight .mini-app-desc {
  color: rgba(255, 255, 255, 0.9);
}

.mini-app-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: #ef4444;
  color: white;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 8px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  color: white;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  margin: 0 0 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
  margin: 0;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.btn:hover {
  transform: translateY(-2px);
}

.btn--ghost {
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid #e2e8f0;
  color: #64748b;
}

.btn--ghost:hover {
  border-color: #667eea;
  color: #667eea;
}

@media (max-width: 768px) {
  .dashboard__header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .header-content {
    flex-direction: column;
  }

  .mini-app-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
