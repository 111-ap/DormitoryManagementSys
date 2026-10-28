<template>
  <div class="page-shell">
    <PageHeader
      eyebrow="Accommodation"
      title="住宿分配"
      subtitle="为新生分配床位，处理调宿与退宿；所有历史记录都会保留。"
    >
      <el-button plain @click="excelApi.assignmentsTemplate()">
        <el-icon><Download /></el-icon>分配模板
      </el-button>
      <el-button plain @click="excelApi.exportAssignments()">
        <el-icon><Document /></el-icon>导出
      </el-button>
      <el-button type="primary" @click="openAssign">
        <el-icon><Plus /></el-icon>分配宿舍
      </el-button>
    </PageHeader>

    <div class="panel panel-pad">
      <div class="toolbar">
        <el-select v-model="filters.status" clearable placeholder="全部状态" style="width: 150px" @change="load">
          <el-option label="在住" value="active" />
          <el-option label="调宿中" value="transferring" />
          <el-option label="已退宿" value="checked_out" />
        </el-select>
        <el-select v-model="filters.room_id" clearable filterable placeholder="全部房间" style="width: 180px" @change="load">
          <el-option v-for="room in rooms" :key="room.id" :label="`${room.building_name} · ${room.room_no}`" :value="room.id" />
        </el-select>
        <el-button @click="load"><el-icon><Refresh /></el-icon>刷新</el-button>
        <div class="toolbar-spacer" />
        <span class="muted">共 {{ total }} 条住宿记录</span>
      </div>

      <el-table v-loading="loading" :data="rows" style="margin-top: 14px">
        <el-table-column prop="student_no" label="学号" min-width="130" />
        <el-table-column prop="student_name" label="姓名" min-width="100" />
        <el-table-column prop="building_name" label="楼栋" min-width="100" />
        <el-table-column prop="room_no" label="房间" width="85" />
        <el-table-column prop="bed_no" label="床位" width="85" />
        <el-table-column label="入住时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.check_in_at) }}</template>
        </el-table-column>
        <el-table-column label="退宿时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.check_out_at) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><StatusTag :value="row.status" /></template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status !== 'checked_out'">
              <el-button link type="primary" @click="openTransfer(row)">调宿</el-button>
              <el-button link type="danger" @click="checkout(row)">退宿</el-button>
            </template>
            <span v-else class="muted">已结束</span>
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

    <el-dialog v-model="assignVisible" title="分配宿舍" width="480px" destroy-on-close>
      <el-form ref="assignFormRef" :model="assignForm" :rules="assignRules" label-position="top">
        <el-form-item label="学生" prop="student_id">
          <el-select v-model="assignForm.student_id" filterable placeholder="选择未分配学生" style="width: 100%">
            <el-option
              v-for="student in availableStudents"
              :key="student.id"
              :label="`${student.student_no} · ${student.name}`"
              :value="student.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="房间" prop="room_id">
          <el-select v-model="assignForm.room_id" filterable placeholder="选择房间" style="width: 100%">
            <el-option
              v-for="room in availableRooms"
              :key="room.id"
              :label="`${room.building_name} · ${room.room_no}（空 ${room.available_beds}）`"
              :value="room.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="床位号" prop="bed_no">
          <el-input v-model="assignForm.bed_no" placeholder="例如 1、2、A" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitAssign">确认分配</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="transferVisible" title="调整宿舍" width="480px" destroy-on-close>
      <p class="muted" style="margin-top: 0">
        将 {{ transferTarget?.student_name }} 从 {{ transferTarget?.building_name }} {{ transferTarget?.room_no }} 调整到新房间。
      </p>
      <el-form ref="transferFormRef" :model="transferForm" :rules="transferRules" label-position="top">
        <el-form-item label="新房间" prop="new_room_id">
          <el-select v-model="transferForm.new_room_id" filterable placeholder="选择房间" style="width: 100%">
            <el-option
              v-for="room in availableRooms"
              :key="room.id"
              :label="`${room.building_name} · ${room.room_no}（空 ${room.available_beds}）`"
              :value="room.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="新床位号" prop="new_bed_no">
          <el-input v-model="transferForm.new_bed_no" placeholder="例如 1、2、A" />
        </el-form-item>
        <el-form-item label="调宿原因">
          <el-input v-model="transferForm.reason" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="transferVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitTransfer">确认调宿</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import PageHeader from '@/components/PageHeader.vue'
import StatusTag from '@/components/StatusTag.vue'
import { assignmentApi, excelApi, roomApi, studentApi } from '@/api'
import { formatDateTime } from '@/utils/constants'

const rows = ref([])
const students = ref([])
const rooms = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const saving = ref(false)
const filters = reactive({ status: '', room_id: null })

const assignVisible = ref(false)
const transferVisible = ref(false)
const transferTarget = ref(null)
const assignFormRef = ref()
const transferFormRef = ref()
const assignForm = reactive({ student_id: null, room_id: null, bed_no: '' })
const transferForm = reactive({ new_room_id: null, new_bed_no: '', reason: '' })
const assignRules = {
  student_id: [{ required: true, message: '请选择学生', trigger: 'change' }],
  room_id: [{ required: true, message: '请选择房间', trigger: 'change' }],
  bed_no: [{ required: true, message: '请输入床位号', trigger: 'blur' }],
}
const transferRules = {
  new_room_id: [{ required: true, message: '请选择新房间', trigger: 'change' }],
  new_bed_no: [{ required: true, message: '请输入新床位号', trigger: 'blur' }],
}

const availableStudents = computed(() => students.value.filter((item) => !item.room_no))
const availableRooms = computed(() => rooms.value.filter((item) => item.status === 'normal'))

async function load() {
  loading.value = true
  try {
    const { data } = await assignmentApi.list({
      page: page.value,
      page_size: pageSize.value,
      status: filters.status || undefined,
      room_id: filters.room_id || undefined,
    })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  const [studentRes, roomRes] = await Promise.all([
    studentApi.list({ page_size: 100 }),
    roomApi.list({ page_size: 100 }),
  ])
  students.value = studentRes.data.items
  rooms.value = roomRes.data.items
}

function openAssign() {
  Object.assign(assignForm, { student_id: null, room_id: null, bed_no: '' })
  assignVisible.value = true
}

function openTransfer(row) {
  transferTarget.value = row
  Object.assign(transferForm, { new_room_id: null, new_bed_no: '', reason: '' })
  transferVisible.value = true
}

async function submitAssign() {
  try {
    await assignFormRef.value.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    await assignmentApi.create(assignForm)
    ElMessage.success('分配成功')
    assignVisible.value = false
    await Promise.all([load(), loadOptions()])
  } finally {
    saving.value = false
  }
}

async function submitTransfer() {
  try {
    await transferFormRef.value.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    await assignmentApi.transfer(transferTarget.value.id, transferForm)
    ElMessage.success('调宿成功')
    transferVisible.value = false
    await Promise.all([load(), loadOptions()])
  } finally {
    saving.value = false
  }
}

async function checkout(row) {
  try {
    await ElMessageBox.confirm(
      `确认让「${row.student_name}」退宿 ${row.building_name} ${row.room_no} 吗？`,
      '退宿确认',
      { type: 'warning' },
    )
    await assignmentApi.checkout(row.id)
    ElMessage.success('退宿成功')
    await Promise.all([load(), loadOptions()])
  } catch {
    // 取消
  }
}

onMounted(async () => {
  await loadOptions()
  await load()
})
</script>
