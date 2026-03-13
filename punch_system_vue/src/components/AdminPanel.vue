<template>
  <div class="admin">
    <div class="admin__header">
      <div>
        <h1 class="admin__title">管理员控制台</h1>
        <p class="admin__sub">查看用户分数与打卡记录（分数通过签到自动获得）</p>
      </div>
      <button class="btn btn--ghost" type="button" @click="$emit('logout')">
        退出登录
      </button>
    </div>

    <div class="admin__content">
      <section class="card">
        <div class="card__head">
          <h2 class="card__title">用户列表</h2>
          <button class="btn btn--ghost" type="button" :disabled="loading" @click="loadUsers">
            {{ loading ? '加载中…' : '刷新' }}
          </button>
        </div>

        <div class="tableWrap">
          <table class="table">
            <thead>
              <tr>
                <th style="width: 72px">ID</th>
                <th>用户名</th>
                <th style="width: 120px">分数</th>
                <th style="width: 150px">签到次数</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td class="mono">{{ user.id }}</td>
                <td>{{ user.username }}</td>
                <td class="mono score">{{ user.score }}</td>
                <td class="mono">{{ getUserPunchCount(user.id) }}</td>
              </tr>
              <tr v-if="users.length === 0">
                <td colspan="4" class="empty">暂无用户</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="card">
        <div class="card__head">
          <h2 class="card__title">打卡记录</h2>
          <button class="btn btn--ghost" type="button" :disabled="recordsLoading" @click="loadRecords">
            {{ recordsLoading ? '加载中…' : '刷新' }}
          </button>
        </div>

        <div class="tableWrap">
          <table class="table">
            <thead>
              <tr>
                <th style="width: 72px">ID</th>
                <th>用户名</th>
                <th>打卡时间</th>
                <th style="width: 90px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="record in records" :key="record.id">
                <td class="mono">{{ record.id }}</td>
                <td>{{ record.username }}</td>
                <td class="mono">{{ formatTime(record.punch_time) }}</td>
                <td>
                  <button class="btn btn--small btn--danger" type="button" :disabled="recordsLoading" @click="deleteRecord(record.id)">
                    删除
                  </button>
                </td>
              </tr>
              <tr v-if="records.length === 0">
                <td colspan="4" class="empty">暂无记录</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <div v-if="message" class="alert" :class="`alert--${messageType}`">
      {{ message }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAllUsers, getAllRecords, deleteRecord as deleteRecordApi } from '../lib/api'

const props = defineProps({
  token: { type: String, required: true }
})

const emit = defineEmits(['logout'])

const users = ref([])
const records = ref([])
const loading = ref(false)
const recordsLoading = ref(false)
const message = ref('')
const messageType = ref('info')

async function loadUsers() {
  loading.value = true
  try {
    const data = await getAllUsers({ token: props.token })
    if (data.code === 200) {
      users.value = data.data || []
    } else {
      message.value = data.msg || '加载用户列表失败'
      messageType.value = 'error'
    }
  } catch (err) {
    message.value = `加载失败：${err?.message || '未知错误'}`
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}

async function loadRecords() {
  recordsLoading.value = true
  try {
    const data = await getAllRecords({ token: props.token })
    if (data.code === 200) {
      records.value = data.data || []
    } else {
      message.value = data.msg || '加载打卡记录失败'
      messageType.value = 'error'
    }
  } catch (err) {
    message.value = `加载失败：${err?.message || '未知错误'}`
    messageType.value = 'error'
  } finally {
    recordsLoading.value = false
  }
}

function getUserPunchCount(userId) {
  return records.value.filter(r => r.user_id === userId).length
}

async function deleteRecord(recordId) {
  if (!confirm('确定要删除这条打卡记录吗？')) return
  
  recordsLoading.value = true
  message.value = ''
  try {
    const data = await deleteRecordApi({ token: props.token, recordId })
    if (data.code === 200) {
      message.value = '删除成功'
      messageType.value = 'success'
      await loadRecords()
    } else {
      message.value = data.msg || '删除失败'
      messageType.value = 'error'
    }
  } catch (err) {
    message.value = `删除失败：${err?.message || '未知错误'}`
    messageType.value = 'error'
  } finally {
    recordsLoading.value = false
  }
}

function formatTime(timeStr) {
  return timeStr.replace('T', ' ')
}

onMounted(() => {
  loadUsers()
  loadRecords()
})
</script>

<style scoped>
.admin {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.admin__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.admin__title {
  margin: 0;
  font-size: 24px;
  letter-spacing: 0.2px;
}

.admin__sub {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: 13px;
}

.admin__content {
  display: grid;
  gap: 20px;
}

.card {
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(229, 231, 235, 0.9);
  border-radius: 16px;
  box-shadow: var(--shadow-strong);
  backdrop-filter: blur(10px);
  padding: 18px;
}

.card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.card__title {
  margin: 0;
  font-size: 16px;
  letter-spacing: 0.2px;
}

.btn {
  border: 1px solid transparent;
  border-radius: 12px;
  padding: 10px 12px;
  font-weight: 800;
  background: var(--primary);
  color: var(--primary-ink);
  transition: transform 0.16s ease, filter 0.16s ease;
}

.btn:hover {
  transform: translateY(-1px);
  filter: saturate(1.1);
}

.btn:active {
  transform: translateY(0);
}

.btn--ghost {
  background: rgba(255, 255, 255, 0.55);
  border-color: rgba(229, 231, 235, 0.9);
  color: var(--text);
}

.btn--ghost:hover {
  border-color: rgba(203, 213, 225, 0.95);
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.tableWrap {
  border: 1px solid rgba(229, 231, 235, 0.9);
  border-radius: 12px;
  overflow: auto;
  background: rgba(255, 255, 255, 0.75);
}

.table {
  width: 100%;
  border-collapse: collapse;
  min-width: 600px;
}

th,
td {
  padding: 12px 12px;
  border-bottom: 1px solid var(--border);
  text-align: left;
  font-size: 13px;
}

thead th {
  position: sticky;
  top: 0;
  background: rgba(248, 250, 252, 0.9);
  color: #0b1220;
  font-weight: 800;
  z-index: 1;
}

tbody tr:hover td {
  background: #f8fafc;
}

.mono {
  font-variant-numeric: tabular-nums;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
    "Liberation Mono", "Courier New", monospace;
}

.score {
  font-weight: 800;
  color: var(--primary);
}

.empty {
  text-align: center;
  color: var(--muted);
  padding: 18px 12px;
}

.alert {
  margin-top: 16px;
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
