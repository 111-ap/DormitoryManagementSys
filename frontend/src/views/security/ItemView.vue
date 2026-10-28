<template>
  <div class="page-shell">
    <PageHeader
      eyebrow="Security"
      title="物品出入"
      subtitle="学生登记带入/带出物品，楼管审核后形成出入记录。"
    >
      <el-button v-if="auth.isStudent" type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>登记物品
      </el-button>
    </PageHeader>

    <div class="panel panel-pad">
      <div class="toolbar">
        <el-select v-model="filters.status" clearable placeholder="全部审核状态" style="width: 150px" @change="load">
          <el-option label="待审核" value="pending" />
          <el-option label="已通过" value="approved" />
          <el-option label="已驳回" value="rejected" />
        </el-select>
        <el-select v-model="filters.direction" clearable placeholder="全部方向" style="width: 130px" @change="load">
          <el-option label="带入" value="in" />
          <el-option label="带出" value="out" />
        </el-select>
        <el-button @click="load"><el-icon><Refresh /></el-icon>刷新</el-button>
        <div class="toolbar-spacer" />
        <span class="muted">共 {{ total }} 条记录</span>
      </div>

      <el-table v-loading="loading" :data="rows" style="margin-top: 14px">
        <el-table-column prop="item_name" label="物品" min-width="130" />
        <el-table-column label="数量" width="100">
          <template #default="{ row }">{{ row.quantity }} {{ row.unit || '' }}</template>
        </el-table-column>
        <el-table-column label="方向" width="90">
          <template #default="{ row }">
            <el-tag :type="row.direction === 'in' ? 'success' : 'warning'" effect="plain">
              {{ row.direction === 'in' ? '带入' : '带出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="student_name" label="登记人" width="100" />
        <el-table-column label="房间" min-width="150">
          <template #default="{ row }">{{ row.building_name }} · {{ row.room_no }}</template>
        </el-table-column>
        <el-table-column prop="reason" label="事由" min-width="150" show-overflow-tooltip />
        <el-table-column label="时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.occurred_at) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><StatusTag :value="row.status" /></template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending' && auth.isStaff">
              <el-button link type="success" @click="review(row, 'approved')">通过</el-button>
              <el-button link type="danger" @click="review(row, 'rejected')">驳回</el-button>
            </template>
            <span v-else class="muted">—</span>
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

    <el-dialog v-model="visible" title="登记物品出入" width="520px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="form-grid">
          <el-form-item label="物品名称" prop="item_name">
            <el-input v-model="form.item_name" placeholder="例如 电脑、行李箱" />
          </el-form-item>
          <el-form-item label="数量" prop="quantity">
            <el-input-number v-model="form.quantity" :min="1" :max="10000" style="width: 100%" />
          </el-form-item>
          <el-form-item label="单位">
            <el-input v-model="form.unit" placeholder="台 / 件 / 箱" />
          </el-form-item>
          <el-form-item label="方向">
            <el-select v-model="form.direction" style="width: 100%">
              <el-option label="带入" value="in" />
              <el-option label="带出" value="out" />
            </el-select>
          </el-form-item>
          <el-form-item label="发生时间">
            <el-date-picker
              v-model="form.occurred_at"
              type="datetime"
              value-format="YYYY-MM-DDTHH:mm:ss"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="事由">
            <el-input v-model="form.reason" placeholder="例如 返校、搬出" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">提交登记</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import PageHeader from '@/components/PageHeader.vue'
import StatusTag from '@/components/StatusTag.vue'
import { itemApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime } from '@/utils/constants'

const auth = useAuthStore()
const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const saving = ref(false)
const filters = reactive({ status: '', direction: '' })
const visible = ref(false)
const formRef = ref()
const form = reactive({
  item_name: '',
  quantity: 1,
  unit: '件',
  direction: 'in',
  occurred_at: '',
  reason: '',
})
const rules = {
  item_name: [{ required: true, message: '请输入物品名称', trigger: 'blur' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }],
}

async function load() {
  loading.value = true
  try {
    const { data } = await itemApi.list({
      page: page.value,
      page_size: pageSize.value,
      status: filters.status || undefined,
      direction: filters.direction || undefined,
    })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(form, {
    item_name: '',
    quantity: 1,
    unit: '件',
    direction: 'in',
    occurred_at: '',
    reason: '',
  })
  visible.value = true
}

async function save() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    await itemApi.create({
      item_name: form.item_name,
      quantity: form.quantity,
      unit: form.unit || null,
      direction: form.direction,
      occurred_at: form.occurred_at || null,
      reason: form.reason || null,
    })
    ElMessage.success('登记成功')
    visible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function review(row, status) {
  try {
    let remark = null
    if (status === 'rejected') {
      const result = await ElMessageBox.prompt('请输入驳回原因', '驳回登记', {
        inputPlaceholder: '例如：物品信息不完整',
        inputValidator: (value) => Boolean(value?.trim()) || '请输入原因',
        type: 'warning',
      })
      remark = result.value
    } else {
      await ElMessageBox.confirm(`确认通过「${row.item_name}」的出入登记？`, '审核通过', { type: 'info' })
    }
    await itemApi.review(row.id, { status, remark })
    ElMessage.success('审核完成')
    await load()
  } catch {
    // 取消
  }
}

onMounted(load)
</script>
