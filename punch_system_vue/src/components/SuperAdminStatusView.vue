<template>
  <section class="page">
    <header class="hero">
      <div>
        <p class="eyebrow">Overview</p>
        <h2 class="title">总览</h2>
      </div>
      <button class="ghostBtn" type="button" :disabled="loading" @click="load">
        {{ loading ? '加载中…' : '刷新' }}
      </button>
    </header>

    <section class="toolbar">
      <label class="search">
        <input v-model.trim="keyword" class="searchInput" type="search" placeholder="搜索用户名、记录 ID 或审批人" />
      </label>
    </section>

    <div v-if="message" class="notice" :class="`notice--${messageType}`">{{ message }}</div>

    <section class="list">
      <article v-for="group in filteredGroups" :key="group.userId" class="userCard">
        <button class="summaryRow" type="button" @click="toggleUser(group.userId)">
          <div class="summaryMain">
            <div class="identity">
              <p class="userName">{{ group.username }}</p>
              <p class="userMeta">{{ group.department || '未设置部门' }}</p>
              <p class="userMeta">{{ group.studentNo || '未设置学号' }}</p>
            </div>

            <div class="summaryStats">
              <span class="statPill statPill--neutral">共 {{ group.totalCount }}</span>
              <span class="statPill statPill--approved">通过 {{ group.approvedCount }}</span>
              <span class="statPill statPill--pending">待审 {{ group.pendingCount }}</span>
              <span class="statPill statPill--rejected">驳回 {{ group.rejectedCount }}</span>
            </div>
          </div>

          <span class="expandMark" :class="{ 'expandMark--open': expandedUserId === group.userId }" aria-hidden="true">⌄</span>
        </button>

        <div v-if="expandedUserId === group.userId" class="detailPanel">
          <div class="detailHead">
            <span class="detailTitle">详细记录</span>
          </div>

          <div class="detailTableWrap desktopOnly">
            <table class="detailTable">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>打卡时间</th>
                  <th>状态</th>
                  <th>审批人</th>
                  <th>审批时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="record in group.records" :key="record.id">
                  <td class="mono">{{ record.id }}</td>
                  <td class="mono">{{ record.punchTimeText }}</td>
                  <td>
                    <span class="status" :class="`status--${record.statusKey}`">{{ record.statusText }}</span>
                  </td>
                  <td>{{ record.approved_by_username || '-' }}</td>
                  <td class="mono">{{ record.approvedAtText }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="detailList mobileOnly">
            <article v-for="record in group.records" :key="`m-${record.id}`" class="recordCard">
              <div class="recordTop">
                <span class="recordId">#{{ record.id }}</span>
                <span class="status" :class="`status--${record.statusKey}`">{{ record.statusText }}</span>
              </div>
              <dl class="metaList">
                <div class="metaItem">
                  <dt>打卡时间</dt>
                  <dd>{{ record.punchTimeText }}</dd>
                </div>
                <div class="metaItem">
                  <dt>审批人</dt>
                  <dd>{{ record.approved_by_username || '-' }}</dd>
                </div>
                <div class="metaItem">
                  <dt>审批时间</dt>
                  <dd>{{ record.approvedAtText }}</dd>
                </div>
              </dl>
            </article>
          </div>
        </div>
      </article>

      <div v-if="!filteredGroups.length" class="emptyState">暂无记录</div>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getAllRecords } from '../lib/api'

const props = defineProps({
  token: { type: String, required: true },
  role: { type: String, default: 'user' }
})

const rows = ref([])
const loading = ref(false)
const keyword = ref('')
const message = ref('')
const messageType = ref('info')
const expandedUserId = ref(null)

function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

function normalizeRecord(item) {
  const approved = Number(item.approved ?? 0)
  let statusKey = 'pending'
  let statusText = '待审批'
  if (approved === 1) {
    statusKey = 'approved'
    statusText = '已通过'
  } else if (approved === -1) {
    statusKey = 'rejected'
    statusText = '已驳回'
  }

  return {
    ...item,
    statusKey,
    statusText,
    punchTimeText: formatDateTime(item.punch_time),
    approvedAtText: formatDateTime(item.approved_at)
  }
}

const groupedUsers = computed(() => {
  const groups = new Map()

  rows.value.map(normalizeRecord).forEach((record) => {
    const userId = Number(record.user_id)
    if (!groups.has(userId)) {
      groups.set(userId, {
        userId,
        username: record.username || `用户 ${userId}`,
        studentNo: record.student_no || '',
        department: record.department || '',
        records: [],
        totalCount: 0,
        approvedCount: 0,
        pendingCount: 0,
        rejectedCount: 0,
        latestPunchTimeRaw: record.punch_time || '',
        latestPunchTimeText: formatDateTime(record.punch_time),
        searchText: ''
      })
    }

    const group = groups.get(userId)
    group.records.push(record)
    group.totalCount += 1
    if (record.statusKey === 'approved') group.approvedCount += 1
    if (record.statusKey === 'pending') group.pendingCount += 1
    if (record.statusKey === 'rejected') group.rejectedCount += 1
  })

  const list = Array.from(groups.values()).map((group) => {
    group.searchText = [
      group.username,
      group.department,
      group.studentNo,
      ...group.records.map((record) =>
        `${record.id} ${record.punchTimeText} ${record.statusText} ${record.approved_by_username || ''} ${record.approvedAtText}`
      )
    ]
      .join(' ')
      .toLowerCase()
    return group
  })

  return list.sort((a, b) => new Date(b.latestPunchTimeRaw).getTime() - new Date(a.latestPunchTimeRaw).getTime())
})

const filteredGroups = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  if (!q) return groupedUsers.value
  return groupedUsers.value.filter((group) => group.searchText.includes(q))
})

function toggleUser(userId) {
  expandedUserId.value = expandedUserId.value === userId ? null : userId
}

async function load() {
  loading.value = true
  message.value = ''
  try {
    const data = await getAllRecords({ token: props.token, role: props.role })
    if (data.code === 200) {
      rows.value = data.data || []
      if (expandedUserId.value && !rows.value.some((item) => Number(item.user_id) === expandedUserId.value)) {
        expandedUserId.value = null
      }
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

onMounted(() => {
  load()
})
</script>

<style scoped>
.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 18px 120px;
}

.hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(24, 59, 77, 0.58);
}

.title {
  margin: 0;
  font-size: clamp(34px, 4vw, 56px);
  line-height: 0.98;
  letter-spacing: -0.05em;
  color: #152131;
}

.ghostBtn {
  min-height: 42px;
  padding: 0 16px;
  border: 0;
  border-radius: 999px;
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
  font-size: 12px;
  font-weight: 800;
}

.toolbar {
  display: grid;
  gap: 16px;
  margin-bottom: 16px;
}

.searchInput {
  width: 100%;
  min-height: 52px;
  border-radius: 18px;
  border: 1px solid rgba(24, 33, 47, 0.08);
  background: rgba(255, 255, 255, 0.76);
  padding: 0 16px;
  font-size: 15px;
  color: #18212f;
  outline: none;
  box-sizing: border-box;
  box-shadow: 0 14px 34px rgba(20, 29, 41, 0.05);
}

.notice {
  margin-bottom: 16px;
  padding: 12px 14px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 800;
}

.notice--error {
  background: rgba(239, 68, 68, 0.12);
  color: #991b1b;
}

.list {
  display: grid;
  gap: 14px;
}

.userCard {
  overflow: hidden;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(24, 33, 47, 0.08);
  box-shadow: 0 22px 54px rgba(20, 29, 41, 0.08);
}

.summaryRow {
  width: 100%;
  border: 0;
  background: transparent;
  padding: 18px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  text-align: left;
}

.summaryMain {
  min-width: 0;
  display: grid;
  gap: 10px;
  flex: 1;
}

.identity {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 10px;
  min-width: 0;
}

.userName {
  margin: 0;
  font-size: 22px;
  font-weight: 900;
  letter-spacing: -0.04em;
  color: #152131;
}

.userMeta {
  margin: 0;
  font-size: 13px;
  color: rgba(24, 33, 47, 0.58);
}

.summaryStats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.statPill,
.status {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
}

.statPill--approved,
.status--approved {
  background: rgba(34, 197, 94, 0.14);
  color: #166534;
}

.statPill--neutral {
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
}

.statPill--pending,
.status--pending {
  background: rgba(245, 158, 11, 0.14);
  color: #b45309;
}

.statPill--rejected,
.status--rejected {
  background: rgba(239, 68, 68, 0.14);
  color: #991b1b;
}

.expandMark {
  flex-shrink: 0;
  font-size: 22px;
  line-height: 1;
  color: rgba(24, 59, 77, 0.62);
  transform: rotate(0deg);
  transition: transform 0.18s ease;
}

.expandMark--open {
  transform: rotate(180deg);
}

.detailPanel {
  padding: 0 20px 20px;
  border-top: 1px solid rgba(24, 33, 47, 0.08);
}

.detailHead {
  padding: 14px 0 12px;
}

.detailTitle {
  font-size: 13px;
  font-weight: 800;
  color: rgba(24, 59, 77, 0.58);
}

.detailTableWrap {
  overflow-x: auto;
  border-radius: 22px;
  background: rgba(248, 242, 231, 0.5);
}

.detailTable {
  width: 100%;
  border-collapse: collapse;
}

.detailTable th,
.detailTable td {
  padding: 14px 16px;
  text-align: left;
  border-bottom: 1px solid rgba(24, 33, 47, 0.08);
  vertical-align: middle;
}

.detailTable th {
  font-size: 12px;
  color: rgba(24, 59, 77, 0.56);
  font-weight: 800;
}

.detailTable tbody tr:last-child td {
  border-bottom: 0;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}

.mobileOnly {
  display: none;
}

.emptyState {
  padding: 28px 18px;
  border-radius: 24px;
  text-align: center;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(24, 33, 47, 0.08);
  color: rgba(24, 33, 47, 0.56);
  font-weight: 700;
}

@media (max-width: 900px) {
  .page {
    padding: 20px 14px 120px;
  }

  .hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .summaryRow {
    padding: 16px;
    align-items: flex-start;
  }

  .desktopOnly {
    display: none;
  }

  .mobileOnly {
    display: grid;
    gap: 10px;
  }

  .detailPanel {
    padding: 0 16px 16px;
  }

  .recordCard {
    padding: 14px;
    border-radius: 18px;
    background: rgba(248, 242, 231, 0.56);
  }

  .recordTop {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .recordId {
    font-size: 13px;
    font-weight: 800;
    color: rgba(24, 59, 77, 0.7);
  }

  .metaList {
    display: grid;
    gap: 10px;
    margin: 12px 0 0;
  }

  .metaItem {
    padding: 10px 12px;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.74);
  }

  .metaItem dt {
    margin: 0 0 6px;
    font-size: 11px;
    color: rgba(24, 33, 47, 0.48);
    font-weight: 800;
  }

  .metaItem dd {
    margin: 0;
    font-size: 13px;
    color: rgba(24, 33, 47, 0.82);
    word-break: break-word;
  }
}
</style>
