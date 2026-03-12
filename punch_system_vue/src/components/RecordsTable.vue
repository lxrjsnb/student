<template>
  <section class="card">
    <div class="card__head">
      <div>
        <h2 class="card__title">打卡记录</h2>
        <p class="card__sub">支持按日期筛选与快速刷新。</p>
      </div>
      <button class="btn btn--ghost" type="button" :disabled="loading" @click="$emit('refresh')">
        {{ loading ? '刷新中…' : '刷新' }}
      </button>
    </div>

    <div class="filters">
      <label class="filter">
        <span class="filter__label">开始日期</span>
        <input
          class="filter__input"
          type="date"
          :value="filterStart"
          :disabled="loading"
          @input="$emit('update:filterStart', $event.target.value)"
        />
      </label>
      <label class="filter">
        <span class="filter__label">结束日期</span>
        <input
          class="filter__input"
          type="date"
          :value="filterEnd"
          :disabled="loading"
          @input="$emit('update:filterEnd', $event.target.value)"
        />
      </label>
      <button class="btn btn--ghost" type="button" :disabled="loading" @click="$emit('clearFilters')">
        清空筛选
      </button>
    </div>

    <div class="tableWrap" role="region" aria-label="打卡记录表格" tabindex="0">
      <table class="table">
        <thead>
          <tr>
            <th style="width: 72px">序号</th>
            <th>打卡时间</th>
            <th style="width: 90px">状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(record, idx) in records" :key="record.id ?? idx">
            <td class="mono">{{ idx + 1 }}</td>
            <td class="mono">{{ record.punch_time }}</td>
            <td>
              <span class="tag tag--ok">有效</span>
            </td>
          </tr>
          <tr v-if="recordsLoaded && records.length === 0">
            <td colspan="3" class="empty">暂无记录</td>
          </tr>
          <tr v-if="!recordsLoaded && !loading">
            <td colspan="3" class="empty">请点击“刷新”加载记录</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
defineProps({
  records: { type: Array, required: true },
  recordsLoaded: { type: Boolean, required: true },
  loading: { type: Boolean, default: false },
  filterStart: { type: String, required: true },
  filterEnd: { type: String, required: true }
})

defineEmits(['refresh', 'update:filterStart', 'update:filterEnd', 'clearFilters'])
</script>

<style scoped>
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

.card__sub {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 12px;
}

.filters {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  flex-wrap: wrap;
  padding: 10px 0 12px;
}

.filter {
  display: grid;
  gap: 6px;
}

.filter__label {
  font-size: 12px;
  color: var(--muted);
}

.filter__input {
  padding: 10px 10px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #fff;
}

.btn {
  border: 1px solid transparent;
  border-radius: 12px;
  padding: 10px 12px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--primary), var(--accent), var(--accent2));
  background-size: 200% 200%;
  animation: bgShift 10s ease-in-out infinite;
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

.tableWrap {
  border: 1px solid rgba(229, 231, 235, 0.9);
  border-radius: 12px;
  overflow: auto;
  background: rgba(255, 255, 255, 0.75);
}

.table {
  width: 100%;
  border-collapse: collapse;
  min-width: 420px;
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

.tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
}

.tag--ok {
  background: var(--success-bg);
  color: var(--success-ink);
  border: 1px solid rgba(6, 95, 70, 0.2);
}

.empty {
  text-align: center;
  color: var(--muted);
  padding: 18px 12px;
}
</style>
