<template>
  <div class="page-shell">
    <PageHeader
      eyebrow="Maintenance"
      title="报修工单"
      subtitle="学生提交报修，水电工接单处理并登记解决时间；楼管可查看本楼进度。"
    >
      <el-button plain @click="excelApi.exportRepairs()">
        <el-icon><Document /></el-icon>导出
      </el-button>
      <el-button v-if="canCreate" type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>{{ auth.isStudent ? '提交报修' : '代报修' }}
      </el-button>
    </PageHeader>

    <div class="panel panel-pad">
      <div class="toolbar">
        <el-select v-model="filters.status" clearable placeholder="全部状态" style="width: 140px" @change="load">
          <el-option label="待受理" value="pending" />
          <el-option label="维修中" value="processing" />
          <el-option label="已办结" value="completed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
        <el-select v-model="filters.priority" clearable placeholder="全部优先级" style="width: 140px" @change="load">
          <el-option label="低" value="low" />
          <el-option label="普通" value="normal" />
          <el-option label="高" value="high" />
          <el-option label="紧急" value="urgent" />
        </el-select>
        <el-button @click="load"><el-icon><Refresh /></el-icon>刷新</el-button>
        <div class="toolbar-spacer" />
        <span class="muted">共 {{ total }} 个工单</span>
      </div>

      <el-table v-loading="loading" :data="rows" style="margin-top: 14px" @row-dblclick="openDetail">
        <el-table-column prop="order_no" label="报修单号" min-width="160" />
        <el-table-column label="位置" min-width="140">
          <template #default="{ row }">{{ row.building_name }} · {{ row.room_no }}</template>
        </el-table-column>
        <el-table-column prop="asset_name" label="资产" min-width="110" />
        <el-table-column prop="description" label="故障描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="优先级" width="95">
          <template #default="{ row }">
            <el-tag :type="PRIORITY_TAG_TYPES[row.priority]" effect="light" size="small">
              {{ PRIORITY_LABELS[row.priority] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><StatusTag :value="row.status" /></template>
        </el-table-column>
        <el-table-column prop="reporter_name" label="报修人" width="100" />
        <el-table-column prop="handler_name" label="处理人" width="100" />
        <el-table-column label="报修时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.reported_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button v-if="canAccept(row)" link type="success" @click="accept(row)">接单</el-button>
            <el-button v-if="canComplete(row)" link type="success" @click="openComplete(row)">办结</el-button>
            <el-button v-if="canCancel(row)" link type="danger" @click="cancel(row)">取消</el-button>
          </template>
        </el-table-column>
      </el-table>

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

    <el-dialog v-model="createVisible" :title="auth.isStudent ? '提交报修' : '代学生报修'" width="540px" destroy-on-close>
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-position="top">
        <el-form-item v-if="!auth.isStudent" label="报修房间" prop="room_id">
          <el-select v-model="createForm.room_id" filterable placeholder="选择房间" style="width: 100%">
            <el-option v-for="room in rooms" :key="room.id" :label="`${room.building_name} · ${room.room_no}`" :value="room.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="资产名称" prop="asset_name">
          <el-input v-model="createForm.asset_name" placeholder="例如 吸顶灯、厕所马桶" />
        </el-form-item>
        <el-form-item label="故障描述" prop="description">
          <el-input v-model="createForm.description" type="textarea" :rows="4" maxlength="2000" show-word-limit placeholder="请描述损坏情况" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-radio-group v-model="createForm.priority">
            <el-radio-button value="low">低</el-radio-button>
            <el-radio-button value="normal">普通</el-radio-button>
            <el-radio-button value="high">高</el-radio-button>
            <el-radio-button value="urgent">紧急</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitCreate">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="completeVisible" title="登记维修结果" width="500px" destroy-on-close>
      <el-form ref="completeFormRef" :model="completeForm" :rules="completeRules" label-position="top">
        <el-form-item label="处理方案" prop="solution">
          <el-input v-model="completeForm.solution" type="textarea" :rows="4" placeholder="例如：已更换灯泡并测试正常" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="completeVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitComplete">确认办结</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="报修详情" size="480px">
      <template v-if="detail">
        <div class="detail-head">
          <div>
            <div class="detail-title">{{ detail.asset_name || '未命名资产' }}</div>
            <div class="detail-sub">{{ detail.building_name }} · {{ detail.room_no }} · {{ detail.order_no }}</div>
          </div>
          <StatusTag :value="detail.status" />
        </div>
        <div class="detail-grid">
          <div class="detail-item"><div class="label">报修人</div><div class="value">{{ detail.reporter_name }}</div></div>
          <div class="detail-item"><div class="label">处理人</div><div class="value">{{ detail.handler_name || '未接单' }}</div></div>
          <div class="detail-item"><div class="label">报修时间</div><div class="value">{{ formatDateTime(detail.reported_at) }}</div></div>
          <div class="detail-item"><div class="label">解决时间</div><div class="value">{{ formatDateTime(detail.resolved_at) }}</div></div>
          <div class="detail-item"><div class="label">优先级</div><div class="value">{{ PRIORITY_LABELS[detail.priority] }}</div></div>
        </div>
        <div class="detail-section">
          <div class="label">故障描述</div>
          <p>{{ detail.description }}</p>
        </div>
        <div v-if="detail.solution" class="detail-section">
          <div class="label">处理方案</div>
          <p>{{ detail.solution }}</p>
        </div>
        <div v-if="detail.cancel_reason" class="detail-section">
          <div class="label">取消原因</div>
          <p>{{ detail.cancel_reason }}</p>
        </div>
        <AttachmentPanel biz-type="repair" :biz-id="detail.id" title="报修照片" />
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import AttachmentPanel from '@/components/AttachmentPanel.vue'
import PageHeader from '@/components/PageHeader.vue'
import StatusTag from '@/components/StatusTag.vue'
import { excelApi, repairApi, roomApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import {
  PRIORITY_LABELS,
  PRIORITY_TAG_TYPES,
  formatDateTime,
} from '@/utils/constants'

const auth = useAuthStore()
const rows = ref([])
const rooms = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const saving = ref(false)
const filters = reactive({ status: '', priority: '' })

const createVisible = ref(false)
const completeVisible = ref(false)
const detailVisible = ref(false)
const detail = ref(null)
const completeTarget = ref(null)
const createFormRef = ref()
const completeFormRef = ref()
const createForm = reactive({ room_id: null, asset_name: '', description: '', priority: 'normal' })
const completeForm = reactive({ solution: '' })
const createRules = {
  room_id: [
    {
      validator: (_rule, value, callback) => {
        if (auth.isStudent || value) callback()
        else callback(new Error('请选择房间'))
      },
      trigger: 'change',
    },
  ],
  asset_name: [{ required: true, message: '请输入资产名称', trigger: 'blur' }],
  description: [{ required: true, message: '请描述故障', trigger: 'blur' }],
}
const completeRules = {
  solution: [{ required: true, message: '请输入处理方案', trigger: 'blur' }],
}

const canCreate = computed(
  () => auth.isStudent || ['sys_admin', 'building_admin'].includes(auth.role),
)
const canAccept = (row) =>
  row.status === 'pending' && ['worker', 'sys_admin'].includes(auth.role)
const canComplete = (row) =>
  row.status === 'processing' && ['worker', 'sys_admin'].includes(auth.role)
const canCancel = (row) =>
  !['completed', 'cancelled'].includes(row.status) &&
  (auth.isStudent || ['building_admin', 'sys_admin'].includes(auth.role))

async function loadRooms() {
  if (auth.isStudent) return
  const { data } = await roomApi.list({ page_size: 100 })
  rooms.value = data.items
}

async function load() {
  loading.value = true
  try {
    const { data } = await repairApi.list({
      page: page.value,
      page_size: pageSize.value,
      status: filters.status || undefined,
      priority: filters.priority || undefined,
    })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function openCreate() {
  Object.assign(createForm, {
    room_id: rooms.value[0]?.id || null,
    asset_name: '',
    description: '',
    priority: 'normal',
  })
  createVisible.value = true
}

async function submitCreate() {
  try {
    await createFormRef.value.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    await repairApi.create({
      room_id: auth.isStudent ? null : createForm.room_id,
      asset_name: createForm.asset_name,
      description: createForm.description,
      priority: createForm.priority,
    })
    ElMessage.success('报修已提交')
    createVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function accept(row) {
  try {
    await ElMessageBox.confirm(`确认接单「${row.order_no}」？`, '接单确认', { type: 'info' })
    await repairApi.accept(row.id)
    ElMessage.success('已接单')
    await load()
  } catch {
    // 取消
  }
}

function openComplete(row) {
  completeTarget.value = row
  completeForm.solution = ''
  completeVisible.value = true
}

async function submitComplete() {
  try {
    await completeFormRef.value.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    await repairApi.complete(completeTarget.value.id, { solution: completeForm.solution })
    ElMessage.success('维修已办结')
    completeVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function cancel(row) {
  try {
    const { value } = await ElMessageBox.prompt('请输入取消原因', '取消报修', {
      inputPlaceholder: '例如：问题已自行处理',
      inputValidator: (value) => Boolean(value?.trim()) || '请输入原因',
      type: 'warning',
    })
    await repairApi.cancel(row.id, { reason: value.trim() })
    ElMessage.success('已取消')
    await load()
  } catch {
    // 取消
  }
}

async function openDetail(row) {
  const { data } = await repairApi.get(row.id)
  detail.value = data
  detailVisible.value = true
}

onMounted(async () => {
  await loadRooms()
  await load()
})
</script>

<style scoped>
.detail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid #e2e8f0;
}
.detail-title {
  color: #0f172a;
  font-size: 20px;
  font-weight: 800;
}
.detail-sub {
  margin-top: 5px;
  color: #94a3b8;
  font-size: 11px;
}
.detail-section {
  margin-top: 18px;
}
.detail-section .label {
  margin-bottom: 5px;
  color: #94a3b8;
  font-size: 11px;
}
.detail-section p {
  margin: 0;
  padding: 11px;
  color: #475569;
  background: #f8fafc;
  border-radius: 9px;
  font-size: 12px;
  line-height: 1.7;
  white-space: pre-wrap;
}
:deep(.el-drawer__body) {
  padding-top: 10px;
}
</style>
