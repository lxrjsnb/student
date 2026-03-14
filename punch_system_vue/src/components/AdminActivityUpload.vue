<template>
  <section class="page">
    <header class="head">
      <div>
        <p class="kicker">管理员</p>
        <h2 class="title">活动上传</h2>
        <p class="sub">先本地保存，不写入数据库</p>
      </div>
    </header>

    <div class="card">
      <div class="row">
        <label class="label">活动名称</label>
        <input v-model.trim="name" class="input" placeholder="请输入活动名称" />
      </div>

      <div class="row">
        <label class="label">活动图片</label>
        <input class="input" type="file" accept="image/*" @change="onPick" />
      </div>

      <div v-if="previewUrl" class="preview">
        <img class="previewImg" :src="previewUrl" alt="预览图" />
      </div>

      <button class="btn primary" type="button" :disabled="!canSubmit" @click="save">
        保存
      </button>
    </div>

    <div class="card list">
      <div class="listHead">
        <h3 class="listTitle">已上传</h3>
        <button class="btn ghost" type="button" :disabled="items.length === 0" @click="clearAll">清空</button>
      </div>

      <div v-if="items.length === 0" class="empty">暂无活动</div>

      <div v-for="item in items" :key="item.id" class="item">
        <img class="thumb" :src="item.imageDataUrl" alt="活动图片" />
        <div class="meta">
          <p class="name">{{ item.name }}</p>
          <p class="time">{{ item.createdAt }}</p>
        </div>
        <button class="btn dangerSmall" type="button" @click="remove(item.id)">删除</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'

const STORAGE_KEY = 'punch_admin_activities_local'

const name = ref('')
const previewUrl = ref('')
const pickedDataUrl = ref('')
const items = ref(loadItems())

const canSubmit = computed(() => name.value && pickedDataUrl.value)

function loadItems() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items.value))
}

function onPick(e) {
  const file = e?.target?.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = () => {
    pickedDataUrl.value = String(reader.result || '')
    previewUrl.value = pickedDataUrl.value
  }
  reader.readAsDataURL(file)
}

function save() {
  if (!canSubmit.value) return
  const now = new Date().toLocaleString('zh-CN', { hour12: false })
  items.value = [
    {
      id: `${Date.now()}_${Math.random().toString(16).slice(2)}`,
      name: name.value,
      imageDataUrl: pickedDataUrl.value,
      createdAt: now
    },
    ...items.value
  ]
  persist()
  name.value = ''
  previewUrl.value = ''
  pickedDataUrl.value = ''
}

function remove(id) {
  items.value = items.value.filter((x) => x.id !== id)
  persist()
}

function clearAll() {
  if (!confirm('确定清空所有本地活动吗？')) return
  items.value = []
  persist()
}
</script>

<style scoped>
.page {
  padding: 18px 16px 92px;
  width: 100%;
}

.head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.kicker {
  margin: 0;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.6);
}

.title {
  margin: 4px 0 0;
  font-size: 18px;
  font-weight: 1000;
  letter-spacing: 0.2px;
  color: rgba(15, 23, 42, 0.9);
}

.sub {
  margin: 8px 0 0;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.62);
}

.card {
  width: 100%;
  max-width: 840px;
  margin: 0 auto 12px;
  border-radius: 20px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.66);
  border: 1px solid rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.14);
  display: grid;
  gap: 10px;
}

.row {
  display: grid;
  gap: 6px;
}

.label {
  font-size: 12px;
  color: rgba(15, 23, 42, 0.62);
  font-weight: 900;
}

.input {
  width: 100%;
  border-radius: 14px;
  padding: 10px 12px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.72);
  color: rgba(15, 23, 42, 0.9);
  outline: none;
}

.btn {
  border: 0;
  border-radius: 16px;
  padding: 12px 14px;
  font-weight: 900;
  cursor: pointer;
}

.ghost {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.06);
  color: rgba(15, 23, 42, 0.78);
}

.primary {
  background: rgba(0, 168, 204, 0.12);
  border: 1px solid rgba(0, 168, 204, 0.18);
  color: rgba(0, 95, 120, 1);
}

.preview {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: rgba(255, 255, 255, 0.7);
}

.previewImg {
  width: 100%;
  max-height: 260px;
  object-fit: cover;
  display: block;
}

.list {
  gap: 12px;
}

.listHead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.listTitle {
  margin: 0;
  font-size: 14px;
  font-weight: 1000;
  color: rgba(15, 23, 42, 0.9);
}

.empty {
  text-align: center;
  color: rgba(15, 23, 42, 0.62);
  font-weight: 900;
  padding: 12px 0;
}

.item {
  display: grid;
  grid-template-columns: 60px 1fr auto;
  gap: 10px;
  align-items: center;
  padding: 10px;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: rgba(255, 255, 255, 0.7);
}

.thumb {
  width: 60px;
  height: 60px;
  border-radius: 14px;
  object-fit: cover;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.meta {
  display: grid;
  gap: 6px;
}

.name {
  margin: 0;
  font-weight: 1000;
  color: rgba(15, 23, 42, 0.9);
}

.time {
  margin: 0;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.62);
}

.dangerSmall {
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.22);
  color: #b91c1c;
}
</style>

