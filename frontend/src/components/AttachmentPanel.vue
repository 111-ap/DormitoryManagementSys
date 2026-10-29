<template>
  <div class="attachment-panel">
    <div class="attachment-head">
      <div>
        <h4>{{ title }}</h4>
        <p>支持 jpg / png / webp，单张不超过 5MB</p>
      </div>
      <el-upload
        :show-file-list="false"
        accept=".jpg,.jpeg,.png,.webp"
        :http-request="handleUpload"
        :before-upload="beforeUpload"
        :disabled="uploading"
      >
        <el-button :loading="uploading" size="small" type="primary" plain>
          <el-icon><Upload /></el-icon>
          上传图片
        </el-button>
      </el-upload>
    </div>

    <div v-if="files.length" class="attachment-list">
      <div v-for="file in files" :key="file.id" class="attachment-item">
        <div class="file-icon"><el-icon><Picture /></el-icon></div>
        <div class="file-meta">
          <div class="file-name">{{ file.file_name }}</div>
          <div class="file-sub">{{ prettySize(file.file_size) }}</div>
        </div>
        <div class="file-actions">
          <el-button link type="primary" @click="download(file)">下载</el-button>
          <el-button link type="danger" @click="remove(file)">删除</el-button>
        </div>
      </div>
    </div>
    <el-empty v-else :image-size="56" description="暂无附件" />
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { attachmentApi } from '@/api'

const props = defineProps({
  bizType: { type: String, required: true },
  bizId: { type: [Number, String], required: true },
  title: { type: String, default: '现场照片' },
})

const files = ref([])
const uploading = ref(false)

function prettySize(size) {
  const value = Number(size || 0)
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / 1024 / 1024).toFixed(2)} MB`
}

async function load() {
  if (!props.bizId) return
  try {
    const { data } = await attachmentApi.list(props.bizType, props.bizId)
    files.value = data
  } catch {
    files.value = []
  }
}

function beforeUpload(file) {
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.warning('图片不能超过 5MB')
    return false
  }
  return true
}

async function handleUpload(options) {
  uploading.value = true
  try {
    await attachmentApi.upload(props.bizType, props.bizId, options.file)
    ElMessage.success('上传成功')
    await load()
  } finally {
    uploading.value = false
  }
}

async function download(file) {
  await attachmentApi.download(file.id, file.file_name)
}

async function remove(file) {
  await ElMessageBox.confirm(`确定删除「${file.file_name}」吗？`, '删除附件', {
    type: 'warning',
  })
  await attachmentApi.remove(file.id)
  ElMessage.success('已删除')
  await load()
}

watch(() => [props.bizType, props.bizId], load)
onMounted(load)
</script>

<style scoped>
.attachment-panel {
  padding: 14px;
  background: #f7f7f7;
  border: 1px solid #e7e7e7;
  border-radius: 3px;
}
.attachment-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.attachment-head h4 {
  margin: 0;
  font-size: 14px;
}
.attachment-head p {
  margin: 4px 0 0;
  color: #94a3b8;
  font-size: 11px;
}
.attachment-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}
.attachment-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  background: #fff;
  border: 1px solid #e7e7e7;
  border-radius: 3px;
}
.file-icon {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  color: #666666;
  background: transparent;
  border: 1px solid #e5e5e5;
  border-radius: 2px;
  font-size: 14px;
}
.file-meta {
  min-width: 0;
  flex: 1;
}
.file-name {
  overflow: hidden;
  font-size: 12px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-sub {
  margin-top: 2px;
  color: #94a3b8;
  font-size: 11px;
}
.file-actions {
  display: flex;
  gap: 2px;
}
</style>
