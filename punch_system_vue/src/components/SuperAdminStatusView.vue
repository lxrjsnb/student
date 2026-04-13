<template>
  <section class="page">
    <template v-if="selectedUser">
      <header class="hero hero--detail">
        <div class="hero__main">
          <div class="heroLead">
            <button class="back" type="button" aria-label="返回总览" title="返回总览" @click="backToList">
              <svg class="back__icon" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M14.5 5.5L8.5 12L14.5 18.5" />
              </svg>
            </button>
          </div>
          <div class="titleRow">
            <h2 class="title">{{ selectedUser.username }}</h2>
            <p class="subtitle subtitle--inline">
              {{ selectedUser.department || '未设置部门' }}
              <span class="subtitle__dot">•</span>
              {{ selectedUser.studentNo || '未设置学号' }}
            </p>
          </div>
        </div>
      </header>

      <div v-if="message" class="notice" :class="`notice--${messageType}`">{{ message }}</div>

      <section class="detailPanel">
        <div class="sectionHead">
          <div>
            <p class="sectionEyebrow">Records</p>
            <h3 class="sectionTitle">个人记录</h3>
          </div>
        </div>

        <div class="detailToolbar">
          <label class="searchField detailToolbar__search">
            <span class="searchField__label">搜索</span>
            <input
              v-model.trim="detailKeyword"
              class="searchInput"
              type="search"
              placeholder="搜索打卡时间、状态、审批信息"
            />
          </label>
          <button class="ghostBtn toolbarBtn" type="button" :disabled="loading" @click="load">
            {{ loading ? '刷新中…' : '刷新数据' }}
          </button>
          <label class="detailField">
            <span class="searchField__label">筛选</span>
            <select v-model="detailStatusFilter" class="detailSelect">
              <option value="all">全部状态</option>
              <option value="approved">已通过</option>
              <option value="pending">待审批</option>
              <option value="rejected">已驳回</option>
            </select>
          </label>
          <label class="detailField">
            <span class="searchField__label">排序</span>
            <select v-model="detailSortKey" class="detailSelect">
              <option value="time_desc">打卡时间从新到旧</option>
              <option value="time_asc">打卡时间从旧到新</option>
              <option value="status">按审批状态</option>
            </select>
          </label>
        </div>

        <div class="detailTableWrap desktopOnly">
          <table class="table detailTable">
            <thead>
              <tr>
                <th>打卡时间</th>
                <th>状态</th>
                <th>审批信息</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="record in detailRecords" :key="record.id">
                <td class="mono">{{ record.punchTimeText }}</td>
                <td>
                  <span class="statusPill" :class="`statusPill--${record.statusKey}`">{{ record.statusText }}</span>
                </td>
                <td>{{ formatApprovalInfo(record) }}</td>
              </tr>
              <tr v-if="!detailRecords.length">
                <td colspan="3" class="emptyState">暂无符合条件的记录</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="mobileCards mobileOnly">
          <article v-for="record in detailRecords" :key="`mobile-${record.id}`" class="recordCard">
            <div class="recordCard__top">
              <p class="recordCard__time mono">{{ record.punchTimeText }}</p>
              <span class="statusPill" :class="`statusPill--${record.statusKey}`">{{ record.statusText }}</span>
            </div>
            <p class="recordCard__meta">{{ formatApprovalInfo(record) }}</p>
          </article>
          <div v-if="!detailRecords.length" class="emptyState">暂无符合条件的记录</div>
        </div>
      </section>
    </template>

    <template v-else>
      <header class="hero">
        <div class="hero__main">
          <div>
            <p class="eyebrow">Overview</p>
            <h2 class="title">总览</h2>
            <p class="subtitle">按用户集中查看姓名、部门和已通过打卡数。</p>
          </div>
        </div>
      </header>

      <section class="toolbar">
        <label class="searchField">
          <span class="searchField__label">搜索</span>
          <input
            v-model.trim="keyword"
            class="searchInput"
            type="search"
            placeholder="搜索姓名、部门、学号"
          />
        </label>
        <button class="ghostBtn toolbarBtn" type="button" :disabled="loading" @click="load">
          {{ loading ? '加载中…' : '刷新' }}
        </button>
      </section>

      <div v-if="message" class="notice" :class="`notice--${messageType}`">{{ message }}</div>

      <section class="tablePanel desktopOnly">
        <div class="tableShell">
          <table class="table overviewTable">
            <thead>
              <tr>
                <th>
                  <button class="sortBtn" type="button" @click="changeSort('username')">
                    姓名
                    <span class="sortMark">{{ sortMark('username') }}</span>
                  </button>
                </th>
                <th>
                  <button class="sortBtn" type="button" @click="changeSort('department')">
                    部门
                    <span class="sortMark">{{ sortMark('department') }}</span>
                  </button>
                </th>
                <th>
                  <button class="sortBtn" type="button" @click="changeSort('approvedCount')">
                    通过打卡
                    <span class="sortMark">{{ sortMark('approvedCount') }}</span>
                  </button>
                </th>
                <th>
                  <button class="sortBtn" type="button" @click="changeSort('totalCount')">
                    总记录
                    <span class="sortMark">{{ sortMark('totalCount') }}</span>
                  </button>
                </th>
                <th class="tableAction">详情</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in filteredUsers" :key="user.userId">
                <td>{{ user.username }}</td>
                <td>{{ user.department || '未设置部门' }}</td>
                <td class="mono">{{ user.approvedCount }}</td>
                <td class="mono">{{ user.totalCount }}</td>
                <td class="tableAction">
                  <button class="openBtn" type="button" @click="openUserDetail(user)">查看详情</button>
                </td>
              </tr>
              <tr v-if="!filteredUsers.length">
                <td colspan="5" class="emptyState">暂无符合条件的成员</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="tablePanel mobileOnly">
        <div class="tableShell tableShell--mobile">
          <table class="table overviewTable overviewTable--mobile">
            <thead>
              <tr>
                <th>
                  <button class="sortBtn" type="button" @click="changeSort('username')">
                    姓名
                    <span class="sortMark">{{ sortMark('username') }}</span>
                  </button>
                </th>
                <th>
                  <button class="sortBtn" type="button" @click="changeSort('department')">
                    部门
                    <span class="sortMark">{{ sortMark('department') }}</span>
                  </button>
                </th>
                <th>
                  <button class="sortBtn" type="button" @click="changeSort('approvedCount')">
                    通过
                    <span class="sortMark">{{ sortMark('approvedCount') }}</span>
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="user in filteredUsers"
                :key="`mobile-row-${user.userId}`"
                class="tableRowButton"
                tabindex="0"
                @click="openUserDetail(user)"
                @keydown.enter.prevent="openUserDetail(user)"
                @keydown.space.prevent="openUserDetail(user)"
              >
                <td>{{ user.username }}</td>
                <td>{{ user.department || '未设置部门' }}</td>
                <td class="mono">{{ user.approvedCount }}</td>
              </tr>
              <tr v-if="!filteredUsers.length">
                <td colspan="3" class="emptyState">暂无符合条件的成员</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getAllRecords, getAllUsers } from '../lib/api'

const props = defineProps({
  token: { type: String, required: true },
  role: { type: String, default: 'user' }
})

const loading = ref(false)
const keyword = ref('')
const message = ref('')
const messageType = ref('info')
const users = ref([])
const records = ref([])
const selectedUserId = ref(null)
const sortKey = ref('approvedCount')
const sortDirection = ref('desc')
const detailKeyword = ref('')
const detailStatusFilter = ref('all')
const detailSortKey = ref('time_desc')

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
    userId: Number(item.user_id || 0),
    statusKey,
    statusText,
    punchTimeText: formatDateTime(item.punch_time),
    approvedAtText: formatDateTime(item.approved_at)
  }
}

function formatApprovalInfo(record) {
  const approver = record?.approved_by_username || '-'
  const approvedAt = record?.approvedAtText || '-'
  if (approver === '-' && approvedAt === '-') return '-'
  return `${approver} · ${approvedAt}`
}

const recordsByUser = computed(() => {
  const groups = new Map()
  for (const record of records.value.map(normalizeRecord)) {
    const key = Number(record.userId || 0)
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key).push(record)
  }
  for (const [, list] of groups) {
    list.sort((a, b) => new Date(b.punch_time || 0).getTime() - new Date(a.punch_time || 0).getTime())
  }
  return groups
})

const userSummaries = computed(() => {
  return (users.value || [])
    .filter((user) => (user.role || 'user') === 'user')
    .map((user) => {
    const userId = Number(user.id || 0)
    const userRecords = recordsByUser.value.get(userId) || []
    const approvedCount = userRecords.filter((item) => item.statusKey === 'approved').length
    const pendingCount = userRecords.filter((item) => item.statusKey === 'pending').length
    const rejectedCount = userRecords.filter((item) => item.statusKey === 'rejected').length
    const latestPunchTimeRaw = userRecords[0]?.punch_time || ''

    return {
      userId,
      username: user.nickname || user.username || `用户 ${userId}`,
      rawUsername: user.username || '',
      department: user.department || '',
      studentNo: user.student_no || '',
      role: user.role || 'user',
      approvedCount,
      pendingCount,
      rejectedCount,
      totalCount: userRecords.length,
      latestPunchTimeRaw,
      latestPunchTimeText: formatDateTime(latestPunchTimeRaw),
      records: userRecords,
      searchText: [
        user.nickname,
        user.username,
        user.department,
        user.student_no
      ].join(' ').toLowerCase()
    }
  })
})

function compareText(a, b) {
  return String(a || '').localeCompare(String(b || ''), 'zh-CN', { sensitivity: 'base' })
}

const filteredUsers = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  const list = !q
    ? userSummaries.value.slice()
    : userSummaries.value.filter((item) => item.searchText.includes(q))

  list.sort((a, b) => {
    let result = 0
    if (sortKey.value === 'username') {
      result = compareText(a.username || a.rawUsername, b.username || b.rawUsername)
    } else if (sortKey.value === 'department') {
      result = compareText(a.department, b.department) || compareText(a.username || a.rawUsername, b.username || b.rawUsername)
    } else if (sortKey.value === 'totalCount') {
      result = a.totalCount - b.totalCount || compareText(a.username || a.rawUsername, b.username || b.rawUsername)
    } else {
      result = a.approvedCount - b.approvedCount || a.totalCount - b.totalCount || compareText(a.username || a.rawUsername, b.username || b.rawUsername)
    }

    return sortDirection.value === 'asc' ? result : -result
  })

  return list
})

const selectedUser = computed(() => {
  if (!selectedUserId.value) return null
  return userSummaries.value.find((item) => item.userId === selectedUserId.value) || null
})

const detailRecords = computed(() => {
  const baseRecords = selectedUser.value?.records || []
  const q = detailKeyword.value.trim().toLowerCase()

  const list = baseRecords.filter((record) => {
    if (detailStatusFilter.value !== 'all' && record.statusKey !== detailStatusFilter.value) {
      return false
    }
    if (!q) return true
    const haystack = [
      record.punchTimeText,
      record.statusText,
      formatApprovalInfo(record)
    ].join(' ').toLowerCase()
    return haystack.includes(q)
  })

  list.sort((a, b) => {
    if (detailSortKey.value === 'time_asc') {
      return new Date(a.punch_time || 0).getTime() - new Date(b.punch_time || 0).getTime()
    }
    if (detailSortKey.value === 'status') {
      const order = { pending: 0, approved: 1, rejected: 2 }
      return (order[a.statusKey] ?? 9) - (order[b.statusKey] ?? 9) || new Date(b.punch_time || 0).getTime() - new Date(a.punch_time || 0).getTime()
    }
    return new Date(b.punch_time || 0).getTime() - new Date(a.punch_time || 0).getTime()
  })

  return list
})

function sortMark(key) {
  if (sortKey.value !== key) return '↕'
  return sortDirection.value === 'asc' ? '↑' : '↓'
}

function changeSort(key) {
  if (sortKey.value === key) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
    return
  }
  sortKey.value = key
  sortDirection.value = ['username', 'department'].includes(key) ? 'asc' : 'desc'
}

function openUserDetail(user) {
  selectedUserId.value = user.userId
  detailKeyword.value = ''
  detailStatusFilter.value = 'all'
  detailSortKey.value = 'time_desc'
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function backToList() {
  selectedUserId.value = null
  detailKeyword.value = ''
  detailStatusFilter.value = 'all'
  detailSortKey.value = 'time_desc'
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function load() {
  loading.value = true
  message.value = ''
  try {
    const [usersRes, recordsRes] = await Promise.all([
      getAllUsers({ token: props.token, role: props.role }),
      getAllRecords({ token: props.token, role: props.role })
    ])

    if (usersRes.code !== 200) {
      message.value = usersRes.msg || '加载用户列表失败'
      messageType.value = 'error'
      return
    }

    if (recordsRes.code !== 200) {
      message.value = recordsRes.msg || '加载打卡记录失败'
      messageType.value = 'error'
      return
    }

    users.value = usersRes.data || []
    records.value = recordsRes.data || []

    if (selectedUserId.value && !users.value.some((item) => Number(item.id || 0) === selectedUserId.value)) {
      selectedUserId.value = null
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
  max-width: 1240px;
  margin: 0 auto;
  padding: 28px 18px 120px;
}

.hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 18px;
}

.hero--detail {
  align-items: flex-start;
}

.hero__main {
  display: grid;
  gap: 12px;
}

.heroLead {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: rgba(24, 59, 77, 0.54);
  line-height: 1;
}

.title {
  margin: 0;
  font-size: clamp(34px, 4vw, 54px);
  line-height: 0.96;
  letter-spacing: -0.05em;
  color: #142232;
}

.titleRow {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 12px;
}

.subtitle {
  margin: 10px 0 0;
  color: rgba(20, 34, 50, 0.66);
  font-size: 14px;
}

.subtitle--inline {
  margin: 0;
}

.subtitle__dot {
  margin: 0 8px;
}

.ghostBtn,
.back,
.openBtn,
.sortBtn {
  appearance: none;
  border: 0;
  font: inherit;
}

.ghostBtn,
.back,
.openBtn {
  min-height: 44px;
  border-radius: 999px;
  padding: 0 16px;
  font-size: 13px;
  font-weight: 800;
  transition: transform 0.18s ease, background 0.18s ease;
}

.ghostBtn {
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
}

.back {
  width: 28px;
  min-height: 28px;
  height: 28px;
  padding: 0;
  border-radius: 999px;
  background: transparent;
  color: rgba(24, 59, 77, 0.54);
  line-height: 1;
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
}

.back__icon {
  display: block;
  width: 18px;
  height: 18px;
  stroke: currentColor;
  stroke-width: 2.6;
  stroke-linecap: round;
  stroke-linejoin: round;
  fill: none;
}

.openBtn {
  background: #183b4d;
  color: #fff;
}

.openBtn--compact {
  min-height: 34px;
  padding: 0 12px;
  font-size: 12px;
}

.openBtn--block {
  width: 100%;
}

.ghostBtn:hover,
.back:hover,
.openBtn:hover {
  transform: translateY(-1px);
}

.statsGrid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.statCard {
  padding: 16px 18px;
  border-radius: 22px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.94), rgba(244, 239, 230, 0.9));
  border: 1px solid rgba(24, 33, 47, 0.08);
  box-shadow: 0 16px 36px rgba(20, 29, 41, 0.06);
}

.statCard__label {
  display: block;
  margin-bottom: 8px;
  color: rgba(24, 59, 77, 0.66);
  font-size: 12px;
  font-weight: 700;
}

.statCard__value {
  display: block;
  color: #142232;
  font-size: 28px;
  line-height: 1;
}

.statCard__value--small {
  font-size: 16px;
  line-height: 1.35;
}

.toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: 14px;
  margin-bottom: 18px;
}

.searchField {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.searchField__label {
  color: rgba(24, 59, 77, 0.68);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.searchInput {
  width: 100%;
  min-height: 52px;
  border-radius: 18px;
  border: 1px solid rgba(24, 33, 47, 0.08);
  background: rgba(255, 255, 255, 0.78);
  padding: 0 16px;
  font-size: 15px;
  color: #18212f;
  outline: none;
  box-sizing: border-box;
  box-shadow: 0 14px 34px rgba(20, 29, 41, 0.05);
}

.toolbarBtn {
  white-space: nowrap;
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

.tablePanel,
.detailPanel {
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(24, 33, 47, 0.08);
  box-shadow: 0 24px 44px rgba(20, 29, 41, 0.07);
  overflow: hidden;
}

.sectionHead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 22px 22px 0;
}

.detailToolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto 180px 200px;
  align-items: end;
  gap: 12px;
  padding: 16px 22px 14px;
}

.detailToolbar__search {
  margin: 0;
}

.detailField {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.detailSelect {
  width: 100%;
  min-height: 52px;
  border-radius: 18px;
  border: 1px solid rgba(24, 33, 47, 0.08);
  background: rgba(255, 255, 255, 0.78);
  padding: 0 16px;
  font-size: 14px;
  color: #18212f;
  outline: none;
  box-sizing: border-box;
  box-shadow: 0 14px 34px rgba(20, 29, 41, 0.05);
}

.sectionEyebrow {
  margin: 0 0 6px;
  font-size: 11px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(24, 59, 77, 0.52);
}

.sectionTitle {
  margin: 0;
  font-size: 24px;
  color: #142232;
}

.tableShell,
.detailTableWrap {
  overflow: auto;
}

.tableShell--mobile {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.table {
  width: 100%;
  min-width: 720px;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: 16px 18px;
  border-bottom: 1px solid rgba(24, 33, 47, 0.08);
  text-align: left;
  vertical-align: middle;
  font-size: 14px;
  color: #1c2838;
}

.table tbody tr:hover {
  background: rgba(245, 240, 231, 0.58);
}

.overviewTable--mobile {
  min-width: 100%;
  table-layout: fixed;
}

.overviewTable--mobile th:nth-child(1),
.overviewTable--mobile td:nth-child(1) {
  width: 38%;
}

.overviewTable--mobile th:nth-child(2),
.overviewTable--mobile td:nth-child(2) {
  width: 38%;
}

.overviewTable--mobile th:nth-child(3),
.overviewTable--mobile td:nth-child(3) {
  width: 24%;
}

.overviewTable--mobile th,
.overviewTable--mobile td {
  white-space: nowrap;
}

.overviewTable--mobile td:nth-child(1),
.overviewTable--mobile td:nth-child(2) {
  overflow: hidden;
  text-overflow: ellipsis;
}

.tableRowButton {
  cursor: pointer;
}

.tableRowButton:focus-visible {
  outline: 2px solid rgba(24, 59, 77, 0.32);
  outline-offset: -2px;
  background: rgba(245, 240, 231, 0.72);
}

.tableAction {
  width: 120px;
}

.sortBtn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  background: transparent;
  color: #183b4d;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  cursor: pointer;
}

.sortMark {
  color: rgba(24, 59, 77, 0.52);
  font-size: 12px;
}

.mono {
  font-variant-numeric: tabular-nums;
}

.statusPill {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
}

.statusPill--approved {
  background: rgba(34, 197, 94, 0.14);
  color: #166534;
}

.statusPill--pending {
  background: rgba(245, 158, 11, 0.16);
  color: #92400e;
}

.statusPill--rejected {
  background: rgba(239, 68, 68, 0.14);
  color: #991b1b;
}

.mobileCards {
  display: grid;
  gap: 12px;
}

.recordCard {
  border-radius: 20px;
  border: 1px solid rgba(24, 33, 47, 0.08);
  background: rgba(255, 255, 255, 0.86);
  padding: 12px 14px;
  box-shadow: 0 16px 30px rgba(20, 29, 41, 0.06);
}

.recordCard__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.recordCard__time {
  margin: 0;
  min-width: 0;
  color: #1c2838;
  font-size: 13px;
  line-height: 1.35;
  word-break: break-word;
}

.recordCard__meta {
  margin: 0;
  color: rgba(28, 40, 56, 0.74);
  font-size: 12px;
  line-height: 1.35;
  word-break: break-word;
}

.emptyState {
  padding: 24px 18px;
  text-align: center;
  color: rgba(24, 59, 77, 0.62);
  font-size: 14px;
}

.desktopOnly {
  display: block;
}

.mobileOnly {
  display: none;
}

@media (max-width: 960px) {
  .statsGrid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 840px) {
  .page {
    padding: 20px 14px 110px;
  }

  .hero,
  .hero--detail {
    display: grid;
    gap: 14px;
  }

  .heroLead {
    gap: 12px;
  }

  .toolbar {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 10px;
  }

  .desktopOnly {
    display: none;
  }

  .mobileOnly {
    display: block;
  }

  .title {
    font-size: clamp(28px, 9vw, 42px);
  }

  .sectionHead {
    padding: 18px 18px 0;
  }

  .detailToolbar {
    grid-template-columns: minmax(0, 1fr) auto;
    padding: 14px 18px 14px;
  }

  .detailToolbar .detailField {
    grid-column: span 1;
  }
}

@media (max-width: 560px) {
  .statsGrid {
    grid-template-columns: 1fr;
  }

  .statCard__value {
    font-size: 24px;
  }

  .toolbarBtn {
    min-height: 52px;
    padding: 0 14px;
  }

  .detailToolbar {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 10px;
    padding-bottom: 12px;
  }

  .detailToolbar .detailField {
    grid-column: span 2;
  }

  .detailSelect {
    min-height: 46px;
    padding: 0 12px;
    font-size: 13px;
  }

  .table.overviewTable--mobile th,
  .table.overviewTable--mobile td {
    padding: 12px 8px;
    font-size: 12px;
  }

  .overviewTable--mobile .sortBtn {
    gap: 4px;
    font-size: 11px;
    letter-spacing: 0.04em;
  }

  .overviewTable--mobile .sortMark {
    font-size: 10px;
  }

  .recordCard__top {
    display: grid;
  }
}
</style>
