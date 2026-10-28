<template>
  <div class="page-shell">
    <PageHeader
      eyebrow="Inbox"
      title="消息通知"
      subtitle="报修、账单、物品审核和公告等业务通知会汇总在这里。"
    >
      <el-button plain :disabled="!unread" @click="readAll">
        <el-icon><Check /></el-icon>全部已读
      </el-button>
    </PageHeader>

    <div class="panel panel-pad">
      <div class="toolbar">
        <el-radio-group v-model="unreadOnly" @change="load">
          <el-radio-button :value="false">全部</el-radio-button>
          <el-radio-button :value="true">未读</el-radio-button>
        </el-radio-group>
        <el-button @click="load"><el-icon><Refresh /></el-icon>刷新</el-button>
        <div class="toolbar-spacer" />
        <span class="muted">{{ unread }} 条未读</span>
      </div>

      <div v-loading="loading" class="notification-feed">
        <div
          v-for="item in rows"
          :key="item.id"
          class="notification-card"
          :class="{ unread: !item.is_read }"
          @click="open(item)"
        >
          <div class="notification-type">
            <el-icon><component :is="iconFor(item.type)" /></el-icon>
          </div>
          <div class="notification-body">
            <div class="notification-head">
              <strong>{{ item.title }}</strong>
              <span>{{ formatDateTime(item.created_at) }}</span>
            </div>
            <p>{{ item.content || '暂无详情' }}</p>
          </div>
          <span v-if="!item.is_read" class="unread-dot" />
        </div>
        <el-empty v-if="!rows.length && !loading" :image-size="80" description="暂无通知" />
      </div>

      <div class="table-footer">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          background
          @current-change="load"
          @size-change="load"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PageHeader from '@/components/PageHeader.vue'
import { notificationApi } from '@/api'
import { formatDateTime } from '@/utils/constants'

const rows = ref([])
const total = ref(0)
const unread = ref(0)
const page = ref(1)
const pageSize = ref(20)
const unreadOnly = ref(false)
const loading = ref(false)

function iconFor(type) {
  return {
    repair: 'Tools',
    utility: 'Lightning',
    notice: 'ChatDotSquare',
    item: 'Suitcase',
    assignment: 'House',
  }[type] || 'Bell'
}

async function load() {
  loading.value = true
  try {
    const [listRes, unreadRes] = await Promise.all([
      notificationApi.list({
        page: page.value,
        page_size: pageSize.value,
        unread_only: unreadOnly.value,
      }),
      notificationApi.unreadCount(),
    ])
    rows.value = listRes.data.items
    total.value = listRes.data.total
    unread.value = unreadRes.data.count || 0
  } finally {
    loading.value = false
  }
}

async function open(item) {
  if (!item.is_read) {
    await notificationApi.read(item.id)
    item.is_read = true
    item.read_at = new Date().toISOString()
    unread.value = Math.max(0, unread.value - 1)
  }
}

async function readAll() {
  await notificationApi.readAll()
  ElMessage.success('全部通知已标记为已读')
  await load()
}

onMounted(load)
</script>

<style scoped>
.notification-feed {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 260px;
  margin-top: 14px;
}
.notification-card {
  position: relative;
  display: flex;
  gap: 12px;
  padding: 14px 16px;
  background: #fff;
  border: 1px solid #edf2f7;
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.18s ease, background 0.18s ease;
}
.notification-card:hover {
  border-color: #b7e3de;
}
.notification-card.unread {
  background: #f6fdfc;
  border-color: #d5f1ed;
}
.notification-type {
  display: grid;
  flex: 0 0 36px;
  width: 36px;
  height: 36px;
  place-items: center;
  color: #0f766e;
  background: #e8f6f4;
  border-radius: 10px;
}
.notification-body {
  min-width: 0;
  flex: 1;
}
.notification-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.notification-head strong {
  color: #334155;
  font-size: 13px;
}
.notification-head span {
  flex: 0 0 auto;
  color: #94a3b8;
  font-size: 10px;
}
.notification-body p {
  margin: 5px 0 0;
  color: #64748b;
  font-size: 11px;
  line-height: 1.6;
}
.unread-dot {
  position: absolute;
  top: 17px;
  right: 14px;
  width: 7px;
  height: 7px;
  background: #14b8a6;
  border-radius: 50%;
}
</style>
