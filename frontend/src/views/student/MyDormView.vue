<template>
  <div class="page-shell">
    <PageHeader
      eyebrow="My Room"
      title="我的宿舍"
      subtitle="查看当前住宿信息、房间电话和水电账户余额。"
    >
      <el-button type="primary" plain @click="router.push('/utilities')">
        <el-icon><Lightning /></el-icon>查看水电
      </el-button>
    </PageHeader>

    <section class="dorm-hero">
      <div class="dorm-hero-main">
        <div class="hero-icon"><el-icon><House /></el-icon></div>
        <div>
          <div class="hero-kicker">当前住宿房间</div>
          <div class="hero-room">
            {{ student?.building_name || '未分配楼栋' }}
            <span v-if="student?.room_no">· {{ student.room_no }}</span>
          </div>
          <div class="hero-sub">
            {{ student?.bed_no ? `床位 ${student.bed_no}` : '尚未分配床位' }}
            <span v-if="assignment"> · 入住于 {{ formatDateTime(assignment.check_in_at) }}</span>
          </div>
        </div>
      </div>
      <div class="hero-balance">
        <div class="hero-kicker">水电余额</div>
        <div class="balance-value">{{ formatMoney(account?.balance) }}</div>
        <el-button link type="primary" @click="router.push('/utilities')">去充值</el-button>
      </div>
    </section>

    <section class="info-grid">
      <div class="panel panel-pad">
        <h3 class="section-title">学籍信息</h3>
        <div class="detail-grid" style="margin-top: 16px">
          <div class="detail-item"><div class="label">学号</div><div class="value">{{ student?.student_no || '—' }}</div></div>
          <div class="detail-item"><div class="label">姓名</div><div class="value">{{ student?.name || auth.displayName }}</div></div>
          <div class="detail-item"><div class="label">院系</div><div class="value">{{ student?.department_name || '—' }}</div></div>
          <div class="detail-item"><div class="label">班级</div><div class="value">{{ student?.class_name || '—' }}</div></div>
          <div class="detail-item"><div class="label">舍长</div><div class="value">{{ student?.is_dorm_leader ? '是' : '否' }}</div></div>
          <div class="detail-item"><div class="label">房间电话</div><div class="value">{{ room?.phone || '—' }}</div></div>
        </div>
      </div>

      <div class="panel panel-pad">
        <h3 class="section-title">快速办理</h3>
        <div class="my-actions">
          <button v-for="item in actions" :key="item.path" class="my-action" @click="router.push(item.path)">
            <span class="my-action-icon"><el-icon><component :is="item.icon" /></el-icon></span>
            <span><strong>{{ item.title }}</strong><small>{{ item.desc }}</small></span>
            <el-icon class="my-action-arrow"><ArrowRight /></el-icon>
          </button>
        </div>
      </div>
    </section>

    <div class="panel panel-pad">
      <div class="panel-head">
        <div>
          <h3 class="section-title">本楼公告</h3>
          <p class="section-desc">与你当前楼栋和寝室相关的通知</p>
        </div>
        <el-button link type="primary" @click="router.push('/notices')">查看全部</el-button>
      </div>
      <div v-if="notices.length" class="notice-grid">
        <div v-for="notice in notices" :key="notice.id" class="notice-card">
          <div class="notice-top">
            <el-tag size="small" effect="plain">{{ notice.scope === 'room' ? '寝室公告' : '楼栋公告' }}</el-tag>
            <span>{{ formatDateTime(notice.published_at) }}</span>
          </div>
          <h4>{{ notice.title }}</h4>
          <p>{{ notice.content }}</p>
          <div class="notice-author">{{ notice.author_name }}</div>
        </div>
      </div>
      <el-empty v-else :image-size="70" description="暂无公告" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import PageHeader from '@/components/PageHeader.vue'
import { assignmentApi, noticeApi, roomApi, studentApi, utilityApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime, formatMoney } from '@/utils/constants'

const router = useRouter()
const auth = useAuthStore()
const student = ref(auth.student)
const assignment = ref(null)
const room = ref(null)
const account = ref(null)
const notices = ref([])

const actions = [
  { title: '提交报修', desc: '资产损坏及时上报', path: '/repairs', icon: 'Tools' },
  { title: '访客登记', desc: '登记来访亲友', path: '/visitors', icon: 'Postcard' },
  { title: '物品出入', desc: '登记带入带出物品', path: '/items', icon: 'Suitcase' },
  { title: '消息通知', desc: '查看最新提醒', path: '/notifications', icon: 'Bell' },
]

async function load() {
  const [studentRes, assignmentRes, accountRes, noticeRes] = await Promise.allSettled([
    studentApi.me(),
    assignmentApi.me(),
    utilityApi.accounts({ page_size: 10 }),
    noticeApi.list({ page_size: 4 }),
  ])
  if (studentRes.status === 'fulfilled') {
    student.value = studentRes.value.data
    auth.student = studentRes.value.data
  }
  if (assignmentRes.status === 'fulfilled') assignment.value = assignmentRes.value.data
  if (accountRes.status === 'fulfilled') account.value = accountRes.value.data.items?.[0] || null
  if (noticeRes.status === 'fulfilled') notices.value = noticeRes.value.data.items || []
  if (student.value?.room_id) {
    try {
      const { data } = await roomApi.get(student.value.room_id)
      room.value = data
    } catch {
      room.value = null
    }
  }
}

onMounted(load)
</script>

<style scoped>
.dorm-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 30px;
  color: #ecfeff;
  background:
    radial-gradient(circle at 82% 12%, rgba(94, 234, 212, 0.28), transparent 18rem),
    linear-gradient(135deg, #0b2a33, #0f4c4f);
  border-radius: 20px;
  box-shadow: 0 18px 40px rgba(8, 47, 51, 0.16);
}
.dorm-hero-main {
  display: flex;
  align-items: center;
  gap: 18px;
}
.hero-icon {
  display: grid;
  width: 62px;
  height: 62px;
  place-items: center;
  color: #062a2d;
  background: linear-gradient(135deg, #5eead4, #14b8a6);
  border-radius: 18px;
  font-size: 30px;
}
.hero-kicker {
  color: #8fc9c5;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
.hero-room {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 850;
  letter-spacing: -0.03em;
}
.hero-sub {
  margin-top: 7px;
  color: #9fc9c8;
  font-size: 12px;
}
.hero-balance {
  text-align: right;
}
.balance-value {
  margin: 8px 0 4px;
  color: #5eead4;
  font-size: 28px;
  font-weight: 800;
}
.info-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(340px, 0.9fr);
  gap: 16px;
}
.my-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 9px;
  margin-top: 14px;
}
.my-action {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 11px;
  text-align: left;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 11px;
  cursor: pointer;
}
.my-action:hover {
  border-color: #a7d9d4;
}
.my-action-icon {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  color: #0f766e;
  background: #e8f6f4;
  border-radius: 8px;
}
.my-action strong {
  display: block;
  color: #334155;
  font-size: 11px;
}
.my-action small {
  display: block;
  margin-top: 2px;
  color: #94a3b8;
  font-size: 9px;
}
.my-action-arrow {
  margin-left: auto;
  color: #cbd5e1;
}
.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.notice-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.notice-card {
  padding: 15px;
  background: #f8fafc;
  border: 1px solid #edf2f7;
  border-radius: 13px;
}
.notice-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: #94a3b8;
  font-size: 10px;
}
.notice-card h4 {
  margin: 10px 0 5px;
  color: #334155;
  font-size: 13px;
}
.notice-card p {
  display: -webkit-box;
  margin: 0;
  overflow: hidden;
  color: #64748b;
  font-size: 11px;
  line-height: 1.6;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}
.notice-author {
  margin-top: 9px;
  color: #94a3b8;
  font-size: 10px;
}
@media (max-width: 900px) {
  .dorm-hero {
    align-items: flex-start;
    flex-direction: column;
  }
  .hero-balance {
    text-align: left;
  }
  .info-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 620px) {
  .notice-grid {
    grid-template-columns: 1fr;
  }
}
</style>
