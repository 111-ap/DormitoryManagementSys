<template>
  <div class="stat-card" :class="`tone-${tone}`">
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
  tone: { type: String, default: 'teal' },
})
</script>

<style scoped>
.stat-card {
  position: relative;
  display: flex;
  gap: 14px;
  min-height: 118px;
  padding: 18px;
  overflow: hidden;
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 16px;
  box-shadow: 0 12px 26px rgba(15, 23, 42, 0.045);
}
.stat-card::after {
  position: absolute;
  right: -24px;
  bottom: -36px;
  width: 104px;
  height: 104px;
  content: '';
  background: currentColor;
  border-radius: 50%;
  opacity: 0.07;
}
.stat-icon {
  display: grid;
  flex: 0 0 42px;
  width: 42px;
  height: 42px;
  place-items: center;
  color: var(--tone);
  background: color-mix(in srgb, var(--tone) 12%, white);
  border-radius: 12px;
  font-size: 20px;
}
.stat-label {
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
}
.stat-value {
  margin-top: 7px;
  color: #0f172a;
  font-size: 27px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.03em;
}
.stat-hint {
  margin-top: 8px;
  color: #94a3b8;
  font-size: 11px;
}
.tone-teal {
  --tone: #0f766e;
}
.tone-blue {
  --tone: #2563eb;
}
.tone-amber {
  --tone: #d97706;
}
.tone-rose {
  --tone: #e11d48;
}
.tone-violet {
  --tone: #7c3aed;
}
.tone-slate {
  --tone: #475569;
}
</style>
