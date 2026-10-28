<template>
  <el-tag :type="tagType" effect="light" round>{{ text }}</el-tag>
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
