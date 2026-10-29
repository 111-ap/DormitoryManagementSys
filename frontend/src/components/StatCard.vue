<template>
  <div class="stat-card">
    <div class="stat-icon">
      <component :is="icon" />
    </div>
    <div class="stat-content">
      <div class="stat-label">{{ label }}</div>
      <div class="stat-value">{{ value }}</div>
      <div v-if="hint" class="stat-hint">{{ hint }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '—' },
  hint: { type: String, default: '' },
  icon: { type: String, default: 'DataLine' },
  tone: { type: String, default: '' },
})
</script>

<style scoped>
.stat-card {
  position: relative;
  display: flex;
  gap: 13px;
  min-height: 108px;
  padding: 17px 18px;
  background: #ffffff;
  border-right: 1px solid var(--dms-line);
}
.stat-card:nth-child(3n),
.stat-card:last-child {
  border-right: 0;
}
.stat-card:nth-child(-n + 3) {
  border-bottom: 1px solid var(--dms-line);
}
.stat-icon {
  flex: 0 0 auto;
  padding-top: 2px;
  color: #8a8a8a;
  font-size: 17px;
  line-height: 1;
}
.stat-content {
  min-width: 0;
}
.stat-label {
  color: var(--dms-muted);
  font-size: 11px;
  font-weight: 500;
}
.stat-value {
  margin-top: 8px;
  overflow: hidden;
  color: var(--dms-ink);
  font-size: 27px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.04em;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.stat-hint {
  margin-top: 7px;
  overflow: hidden;
  color: var(--dms-faint);
  font-size: 10px;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}
@media (max-width: 1100px) {
  .stat-card:nth-child(3n) {
    border-right: 1px solid var(--dms-line);
  }
  .stat-card:nth-child(2n) {
    border-right: 0;
  }
  .stat-card:nth-child(-n + 3) {
    border-bottom: 0;
  }
  .stat-card:nth-child(-n + 2) {
    border-bottom: 1px solid var(--dms-line);
  }
}
@media (max-width: 700px) {
  .stat-card,
  .stat-card:nth-child(2n) {
    border-right: 0;
    border-bottom: 1px solid var(--dms-line);
  }
  .stat-card:last-child {
    border-bottom: 0;
  }
}
</style>
