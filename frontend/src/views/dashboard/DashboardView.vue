<template>
  <div class="page-shell">
    <PageHeader
      eyebrow="Overview"
      :title="`${greeting}，${auth.displayName}`"
      subtitle="这里汇总当前权限范围内的宿舍运行情况。"
    >
      <el-button v-if="!auth.isStudent" type="primary" plain @click="router.push('/utilities')">
        <el-icon><Lightning /></el-icon>水电管理
      </el-button>
      <el-button type="primary" @click="router.push('/repairs')">
        <el-icon><Tools /></el-icon>发起报修
      </el-button>
    </PageHeader>

    <section class="stat-grid">
      <StatCard
        v-for="card in cards"
        :key="card.label"
        :label="card.label"
        :value="card.value"
        :hint="card.hint"
        :icon="card.icon"
        :tone="card.tone"
      />
    </section>

    <section class="dashboard-grid">
      <div class="panel panel-pad chart-panel">
        <div class="panel-head">
          <div>
            <h3 class="section-title">{{ auth.isStudent ? '我的报修状态' : '房间入住概览' }}</h3>
            <p class="section-desc">
              {{ auth.isStudent ? '按报修状态统计' : '按楼栋统计入住人数与可用床位' }}
            </p>
          </div>
          <el-tag type="info" effect="plain">实时数据</el-tag>
        </div>
        <div ref="occupancyRef" class="chart" />
      </div>

      <div class="panel panel-pad chart-panel">
        <div class="panel-head">
          <div>
            <h3 class="section-title">报修状态分布</h3>
            <p class="section-desc">待受理、处理中、已办结与已取消</p>
          </div>
        </div>
        <div ref="repairRef" class="chart" />
      </div>
    </section>

    <section class="dashboard-grid lower">
      <div class="panel panel-pad">
        <div class="panel-head">
          <div>
            <h3 class="section-title">最新公告</h3>
            <p class="section-desc">与你所在楼栋/寝室相关的公告</p>
          </div>
          <el-button link type="primary" @click="router.push('/notices')">查看全部</el-button>
        </div>
        <div v-if="notices.length" class="notice-list">
          <div v-for="notice in notices" :key="notice.id" class="notice-row">
            <div class="notice-dot" />
            <div class="notice-main">
              <div class="notice-title">{{ notice.title }}</div>
              <div class="notice-sub">{{ notice.author_name }} · {{ formatDateTime(notice.published_at) }}</div>
            </div>
            <el-tag size="small" effect="plain" :type="notice.scope === 'room' ? 'success' : 'info'">
              {{ notice.scope === 'room' ? '寝室' : '楼栋' }}
            </el-tag>
          </div>
        </div>
        <el-empty v-else :image-size="64" description="暂无公告" />
      </div>

      <div class="panel panel-pad">
        <div class="panel-head">
          <div>
            <h3 class="section-title">消息提醒</h3>
            <p class="section-desc">报修、账单、审核与公告通知</p>
          </div>
          <el-button link type="primary" @click="router.push('/notifications')">查看全部</el-button>
        </div>
        <div v-if="notifications.length" class="notification-list">
          <div v-for="item in notifications" :key="item.id" class="notification-row">
            <span class="notification-icon"><el-icon><Bell /></el-icon></span>
            <div class="notification-main">
              <div class="notification-title">{{ item.title }}</div>
              <div class="notification-sub">{{ item.content || '暂无详情' }}</div>
            </div>
            <span class="notification-time">{{ formatDateTime(item.created_at) }}</span>
          </div>
        </div>
        <el-empty v-else :image-size="64" description="暂无消息" />
      </div>
    </section>

    <section class="quick-actions">
      <button v-for="action in quickActions" :key="action.path" class="quick-action" @click="router.push(action.path)">
        <span class="quick-icon"><el-icon><component :is="action.icon" /></el-icon></span>
        <span>
          <strong>{{ action.title }}</strong>
          <small>{{ action.desc }}</small>
        </span>
        <el-icon class="quick-arrow"><ArrowRight /></el-icon>
      </button>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'

import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import { dashboardApi, noticeApi, notificationApi, repairApi, roomApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime, formatMoney } from '@/utils/constants'

const router = useRouter()
const auth = useAuthStore()

const stats = reactive({})
const rooms = ref([])
const repairs = ref([])
const notices = ref([])
const notifications = ref([])
const occupancyRef = ref()
const repairRef = ref()
let occupancyChart = null
let repairChart = null

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 12) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const cards = computed(() => {
  if (auth.isStudent) {
    return [
      {
        label: '我的房间',
        value: auth.student?.room_no || '未分配',
        hint: auth.student?.building_name || '等待宿舍分配',
        icon: 'House',
        tone: 'teal',
      },
      { label: '水电余额', value: formatMoney(stats.balance), hint: '房间账户余额', icon: 'Wallet', tone: 'blue' },
      { label: '待缴账单', value: stats.unpaid_bills ?? 0, hint: '未缴费的水电账单', icon: 'Tickets', tone: 'amber' },
      { label: '处理中报修', value: stats.open_repairs ?? 0, hint: '我的未办结报修', icon: 'Tools', tone: 'rose' },
      { label: '未读通知', value: stats.unread_notifications ?? 0, hint: '点击右上角查看', icon: 'Bell', tone: 'violet' },
    ]
  }
  return [
    { label: '楼栋', value: stats.buildings ?? 0, hint: '当前权限范围', icon: 'OfficeBuilding', tone: 'teal' },
    { label: '房间', value: stats.rooms ?? 0, hint: '可管理房间', icon: 'House', tone: 'blue' },
    { label: '在住学生', value: stats.active_students ?? 0, hint: '当前有效住宿记录', icon: 'UserFilled', tone: 'violet' },
    { label: '待处理报修', value: stats.open_repairs ?? 0, hint: '待受理 + 处理中', icon: 'Tools', tone: 'rose' },
    { label: '未缴账单', value: stats.unpaid_bills ?? 0, hint: '需要跟进的水电账单', icon: 'Tickets', tone: 'amber' },
    { label: '账户总余额', value: formatMoney(stats.utility_balance), hint: '房间水电账户合计', icon: 'Wallet', tone: 'slate' },
  ]
})

const quickActions = computed(() => {
  if (auth.isStudent) {
    return [
      { title: '提交报修', desc: '宿舍资产损坏及时上报', path: '/repairs', icon: 'Tools' },
      { title: '水电充值', desc: '查看余额、账单和充值记录', path: '/utilities', icon: 'Lightning' },
      { title: '访客登记', desc: '登记来访亲友信息', path: '/visitors', icon: 'Postcard' },
      { title: '物品出入', desc: '登记带入或带出物品', path: '/items', icon: 'Suitcase' },
    ]
  }
  return [
    { title: '分配宿舍', desc: '为新生或调宿学生安排床位', path: '/assignments', icon: 'Connection' },
    { title: '处理报修', desc: '查看待受理与处理中工单', path: '/repairs', icon: 'Tools' },
    { title: '水电账单', desc: '生成账单、查看欠费与充值', path: '/utilities', icon: 'Lightning' },
    { title: '发布公告', desc: '向本楼或本寝室发布通知', path: '/notices', icon: 'ChatDotSquare' },
  ]
})

function initCharts() {
  if (occupancyRef.value) {
    occupancyChart = echarts.init(occupancyRef.value)
    if (auth.isStudent) {
      const counts = repairStatusCounts()
      occupancyChart.setOption({
        tooltip: { trigger: 'item' },
        color: ['#a3a3a3', '#111111', '#40576b', '#d4d4d4'],
        series: [
          {
            type: 'pie',
            radius: ['48%', '72%'],
            center: ['50%', '50%'],
            avoidLabelOverlap: true,
            itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 0 },
            label: { formatter: '{b}\n{c}', color: '#4a4a4a', fontSize: 11 },
            data: Object.entries(counts).map(([name, value]) => ({ name, value })),
          },
        ],
      })
    } else {
      const byBuilding = new Map()
      for (const room of rooms.value) {
        const key = room.building_name || '未命名楼栋'
        if (!byBuilding.has(key)) byBuilding.set(key, { occupied: 0, capacity: 0 })
        const item = byBuilding.get(key)
        item.occupied += Number(room.occupied_count || 0)
        item.capacity += Number(room.capacity || 0)
      }
      occupancyChart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { bottom: 0, textStyle: { color: '#6b6b6b', fontSize: 11 } },
        grid: { left: 12, right: 18, top: 18, bottom: 38, containLabel: true },
        xAxis: {
          type: 'category',
          data: [...byBuilding.keys()],
          axisLine: { lineStyle: { color: '#dedede' } },
          axisTick: { show: false },
          axisLabel: { color: '#6b6b6b', fontSize: 11 },
        },
        yAxis: {
          type: 'value',
          splitLine: { lineStyle: { color: '#efefef' } },
          axisLabel: { color: '#969696', fontSize: 10 },
        },
        series: [
          {
            name: '在住',
            type: 'bar',
            barWidth: 16,
            itemStyle: { color: '#111111', borderRadius: 0 },
            data: [...byBuilding.values()].map((item) => item.occupied),
          },
          {
            name: '总床位',
            type: 'bar',
            barWidth: 16,
            itemStyle: { color: '#d4d4d4', borderRadius: 0 },
            data: [...byBuilding.values()].map((item) => item.capacity),
          },
        ],
      })
    }
  }

  if (repairRef.value) {
    repairChart = echarts.init(repairRef.value)
    const counts = repairStatusCounts()
    repairChart.setOption({
      tooltip: { trigger: 'item' },
      color: ['#a3a3a3', '#111111', '#40576b', '#d4d4d4'],
      legend: { bottom: 0, textStyle: { color: '#6b6b6b', fontSize: 11 } },
      series: [
        {
          type: 'pie',
          radius: ['42%', '68%'],
          center: ['50%', '46%'],
          itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 0 },
          label: { formatter: '{b}\n{c}', color: '#4a4a4a', fontSize: 11 },
          data: Object.entries(counts).map(([name, value]) => ({ name, value })),
        },
      ],
    })
  }
}

function repairStatusCounts() {
  const labels = { pending: '待受理', processing: '处理中', completed: '已办结', cancelled: '已取消' }
  const counts = { 待受理: 0, 处理中: 0, 已办结: 0, 已取消: 0 }
  for (const item of repairs.value) {
    const label = labels[item.status]
    if (label) counts[label] += 1
  }
  return counts
}

function resizeCharts() {
  occupancyChart?.resize()
  repairChart?.resize()
}

async function load() {
  const requests = await Promise.allSettled([
    dashboardApi.get(),
    roomApi.list({ page_size: 100 }),
    repairApi.list({ page_size: 100 }),
    noticeApi.list({ page_size: 5 }),
    notificationApi.list({ page_size: 5 }),
  ])
  if (requests[0].status === 'fulfilled') Object.assign(stats, requests[0].value.data)
  if (requests[1].status === 'fulfilled') rooms.value = requests[1].value.data.items || []
  if (requests[2].status === 'fulfilled') repairs.value = requests[2].value.data.items || []
  if (requests[3].status === 'fulfilled') notices.value = requests[3].value.data.items || []
  if (requests[4].status === 'fulfilled') notifications.value = requests[4].value.data.items || []
  await nextTick()
  initCharts()
}

onMounted(() => {
  load()
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  occupancyChart?.dispose()
  repairChart?.dispose()
})
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.65fr);
  gap: 16px;
}
.dashboard-grid.lower {
  grid-template-columns: 1fr 1fr;
}
.chart-panel {
  min-width: 0;
}
.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.chart {
  height: 270px;
  margin-top: 8px;
}
.notice-list,
.notification-list {
  display: flex;
  flex-direction: column;
  margin-top: 12px;
}
.notice-row,
.notification-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 4px;
  border-bottom: 1px solid #ededed;
}
.notice-row:last-child,
.notification-row:last-child {
  border-bottom: 0;
}
.notice-dot {
  flex: 0 0 5px;
  width: 5px;
  height: 5px;
  background: #111111;
  border-radius: 50%;
}
.notice-main,
.notification-main {
  min-width: 0;
  flex: 1;
}
.notice-title,
.notification-title {
  overflow: hidden;
  color: #2b2b2b;
  font-size: 12px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.notice-sub,
.notification-sub {
  margin-top: 4px;
  overflow: hidden;
  color: #969696;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.notification-icon {
  display: grid;
  flex: 0 0 26px;
  width: 26px;
  height: 26px;
  place-items: center;
  color: #666666;
  background: transparent;
  border: 1px solid #e5e5e5;
  border-radius: 2px;
  font-size: 13px;
}
.notification-time {
  flex: 0 0 auto;
  color: #a0a0a0;
  font-size: 9px;
}
.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid var(--dms-line);
  border-radius: 5px;
}
.quick-action {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  text-align: left;
  background: transparent;
  border: 0;
  border-right: 1px solid var(--dms-line);
  border-radius: 0;
  cursor: pointer;
  transition: background-color 0.15s ease;
}
.quick-action:last-child {
  border-right: 0;
}
.quick-action:hover {
  background: #fafafa;
}
.quick-icon {
  flex: 0 0 auto;
  color: #737373;
  background: transparent;
  border-radius: 0;
  font-size: 15px;
}
.quick-action strong {
  display: block;
  color: #222222;
  font-size: 11px;
  font-weight: 600;
}
.quick-action small {
  display: block;
  margin-top: 3px;
  color: #999999;
  font-size: 9px;
}
.quick-arrow {
  margin-left: auto;
  color: #c4c4c4;
  font-size: 12px;
}
@media (max-width: 1100px) {
  .dashboard-grid,
  .dashboard-grid.lower {
    grid-template-columns: 1fr;
  }
  .quick-actions {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .quick-action:nth-child(2n) {
    border-right: 0;
  }
  .quick-action:nth-child(-n + 2) {
    border-bottom: 1px solid var(--dms-line);
  }
}
@media (max-width: 640px) {
  .quick-actions {
    grid-template-columns: 1fr;
  }
  .quick-action,
  .quick-action:nth-child(2n) {
    border-right: 0;
    border-bottom: 1px solid var(--dms-line);
  }
  .quick-action:last-child {
    border-bottom: 0;
  }
  .chart {
    height: 230px;
  }
}
</style>
