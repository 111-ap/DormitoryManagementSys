<template>
  <span class="status-tag">
    <i class="status-dot" :class="`dot-${tagType}`" />
    {{ text }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { STATUS_LABELS, STATUS_TAG_TYPES } from '@/utils/constants'

const props = defineProps({
  value: { type: String, default: '' },
  labels: { type: Object, default: () => STATUS_LABELS },
  types: { type: Object, default: () => STATUS_TAG_TYPES },
})

const text = computed(() => props.labels[props.value] || props.value || '—')
const tagType = computed(() => props.types[props.value] || 'info')
</script>

<style scoped>
.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 8px;
  color: #3e3e3e;
  background: #fafafa;
  border: 1px solid #e5e5e5;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 600;
  line-height: 1.4;
  white-space: nowrap;
}
.status-dot {
  width: 5px;
  height: 5px;
  background: #8a8a8a;
  border-radius: 50%;
}
.dot-success {
  background: #38604b;
}
.dot-warning {
  background: #765f35;
}
.dot-danger {
  background: #7d3b3b;
}
.dot-primary {
  background: #40576b;
}
.dot-info {
  background: #8a8a8a;
}
</style>
