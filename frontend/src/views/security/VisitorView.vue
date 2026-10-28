<template>
  <div class="page-shell">
    <PageHeader
      eyebrow="Security"
      title="访客登记"
      subtitle="学生登记来访亲友，离开时及时注销；楼管可查询本楼访客记录。"
    >
      <el-button plain @click="excelApi.exportVisitors()">
        <el-icon><Document /></el-icon>导出
      </el-button>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>登记访客
      </el-button>
    </PageHeader>

    <div class="panel panel-pad">
      <div class="toolbar">
        <el-select v-model="filters.status" clearable placeholder="全部状态" style="width: 140px" @change="load">
          <el-option label="来访中" value="visiting" />
          <el-option label="已离开" value="left" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
        <el-button @click="load"><el-icon><Refresh /></el-icon>刷新</el-button>
        <div class="toolbar-spacer" />
        <span class="muted">共 {{ total }} 条访客记录</span>
      </div>

      <el-table v-loading="loading" :data="rows" style="margin-top: 14px">
        <el-table-column prop="visitor_name" label="访客姓名" width="110" />
        <el-table-column prop="id_no_masked" label="证件号" min-width="150" />
        <el-table-column prop="phone" label="电话" min-width="130" />
        <el-table-column prop="host_student_name" label="被访学生" width="110" />
        <el-table-column label="房间" min-width="150">
          <template #default="{ row }">{{ row.building_name }} · {{ row.room_no }}</template>
        </el-table-column>
        <el-table-column label="来访时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.visit_at) }}</template>
        </el-table-column>
        <el-table-column label="离开时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.leave_at) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><StatusTag :value="row.status" /></template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'visiting'">
              <el-button link type="success" @click="leave(row)">离开</el-button>
              <el-button link type="danger" @click="cancel(row)">取消</el-button>
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

    <el-dialog v-model="visible" title="登记访客" width="540px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="form-grid">
          <el-form-item label="访客姓名" prop="visitor_name">
            <el-input v-model="form.visitor_name" placeholder="访客姓名" />
          </el-form-item>
          <el-form-item label="联系电话">
            <el-input v-model="form.phone" placeholder="手机号" />
          </el-form-item>
          <el-form-item label="证件类型">
            <el-select v-model="form.id_type" style="width: 100%">
              <el-option label="身份证" value="id_card" />
              <el-option label="学生证" value="student_card" />
              <el-option label="其他" value="other" />
            </el-select>
          </el-form-item>
          <el-form-item label="证件号码">
            <el-input v-model="form.id_no" placeholder="仅用于安全管理" />
          </el-form-item>
          <el-form-item v-if="!auth.isStudent" label="被访学生" prop="host_student_id">
            <el-select v-model="form.host_student_id" filterable style="width: 100%">
              <el-option
                v-for="student in studentsWithRoom"
                :key="student.id"
                :label="`${student.student_no} · ${student.name}`"
                :value="student.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="来访事由">
            <el-input v-model="form.reason" placeholder="例如 送书、探访" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">登记</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import PageHeader from '@/components/PageHeader.vue'
import StatusTag from '@/components/StatusTag.vue'
import { excelApi, studentApi, visitorApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime } from '@/utils/constants'

const auth = useAuthStore()
const rows = ref([])
const students = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const saving = ref(false)
const filters = reactive({ status: '' })
const visible = ref(false)
const formRef = ref()
const form = reactive({
  visitor_name: '',
  phone: '',
  id_type: 'id_card',
  id_no: '',
  host_student_id: null,
  reason: '',
})
const rules = {
  visitor_name: [{ required: true, message: '请输入访客姓名', trigger: 'blur' }],
  host_student_id: [
    {
      validator: (_rule, value, callback) => {
        if (auth.isStudent || value) callback()
        else callback(new Error('请选择被访学生'))
      },
      trigger: 'change',
    },
  ],
}
const studentsWithRoom = ref([])

async function loadStudents() {
  if (auth.isStudent) return
  const { data } = await studentApi.list({ page_size: 100 })
  students.value = data.items
  studentsWithRoom.value = data.items.filter((item) => item.room_id)
}

async function load() {
  loading.value = true
  try {
    const { data } = await visitorApi.list({
      page: page.value,
      page_size: pageSize.value,
      status: filters.status || undefined,
    })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(form, {
    visitor_name: '',
    phone: '',
    id_type: 'id_card',
    id_no: '',
    host_student_id: null,
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
    const student = students.value.find((item) => item.id === form.host_student_id)
    await visitorApi.create({
      visitor_name: form.visitor_name,
      phone: form.phone || null,
      id_type: form.id_type,
      id_no: form.id_no || null,
      host_student_id: auth.isStudent ? null : form.host_student_id,
      room_id: auth.isStudent ? null : student?.room_id || null,
      reason: form.reason || null,
    })
    ElMessage.success('访客登记成功')
    visible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function leave(row) {
  try {
    await ElMessageBox.confirm(`确认「${row.visitor_name}」已离开？`, '访客离开', { type: 'info' })
    await visitorApi.leave(row.id)
    ElMessage.success('已登记离开')
    await load()
  } catch {
    // 取消
  }
}

async function cancel(row) {
  try {
    await ElMessageBox.confirm(`确认取消「${row.visitor_name}」的访客登记？`, '取消登记', { type: 'warning' })
    await visitorApi.cancel(row.id)
    ElMessage.success('已取消')
    await load()
  } catch {
    // 取消
  }
}

onMounted(async () => {
  await loadStudents()
  await load()
})
</script>
