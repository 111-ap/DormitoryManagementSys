<template>
  <div class="page-shell">
    <PageHeader
      eyebrow="Accommodation"
      title="学生档案"
      subtitle="维护学生基本信息、院系班级与舍长标记；住宿分配在“住宿分配”中完成。"
    >
      <template v-if="canManage">
        <el-button plain @click="downloadTemplate">
          <el-icon><Download /></el-icon>下载模板
        </el-button>
        <el-button plain @click="openImport">
          <el-icon><Upload /></el-icon>Excel 导入
        </el-button>
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>新建学生
        </el-button>
      </template>
      <el-button plain @click="exportStudents">
        <el-icon><Document /></el-icon>导出
      </el-button>
    </PageHeader>

    <div class="panel panel-pad">
      <div class="toolbar">
        <el-input v-model="filters.keyword" clearable placeholder="学号 / 姓名 / 班级" style="width: 240px" @keyup.enter="load">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="filters.department_id" clearable placeholder="全部院系" style="width: 190px" @change="load">
          <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
        </el-select>
        <el-select v-model="filters.status" clearable placeholder="全部状态" style="width: 140px" @change="load">
          <el-option label="在校" value="active" />
          <el-option label="毕业" value="graduated" />
          <el-option label="休学" value="suspended" />
        </el-select>
        <el-button @click="load"><el-icon><Refresh /></el-icon>刷新</el-button>
        <div class="toolbar-spacer" />
        <span class="muted">共 {{ total }} 名学生</span>
      </div>

      <el-table v-loading="loading" :data="rows" style="margin-top: 14px">
        <el-table-column prop="student_no" label="学号" min-width="130" />
        <el-table-column prop="name" label="姓名" min-width="100" />
        <el-table-column label="性别" width="80">
          <template #default="{ row }">{{ GENDER_LABELS[row.gender] }}</template>
        </el-table-column>
        <el-table-column prop="department_name" label="院系" min-width="180" show-overflow-tooltip />
        <el-table-column prop="class_name" label="班级" min-width="120" />
        <el-table-column prop="phone" label="电话" min-width="130" />
        <el-table-column label="住宿" min-width="160">
          <template #default="{ row }">
            <span v-if="row.building_name">{{ row.building_name }} · {{ row.room_no }} · {{ row.bed_no }}</span>
            <el-tag v-else size="small" type="info" effect="plain">未分配</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="舍长" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_dorm_leader" type="success" size="small">是</el-tag>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }"><StatusTag :value="row.status" /></template>
        </el-table-column>
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <template v-if="canManage">
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button v-if="!row.user_id" link type="success" @click="createAccount(row)">创建账号</el-button>
            </template>
            <span v-else class="muted">只读</span>
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

    <el-dialog v-model="visible" :title="editing ? '编辑学生' : '新建学生'" width="600px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="form-grid">
          <el-form-item label="学号" prop="student_no">
            <el-input v-model="form.student_no" :disabled="editing" placeholder="唯一学号" />
          </el-form-item>
          <el-form-item label="姓名" prop="name">
            <el-input v-model="form.name" placeholder="学生姓名" />
          </el-form-item>
          <el-form-item label="性别">
            <el-select v-model="form.gender" style="width: 100%">
              <el-option label="男" value="male" />
              <el-option label="女" value="female" />
              <el-option label="其他" value="other" />
            </el-select>
          </el-form-item>
          <el-form-item label="院系">
            <el-select v-model="form.department_id" style="width: 100%" clearable>
              <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="班级">
            <el-input v-model="form.class_name" placeholder="例如 软件 2601" />
          </el-form-item>
          <el-form-item label="联系电话">
            <el-input v-model="form.phone" placeholder="手机号" />
          </el-form-item>
          <el-form-item label="舍长">
            <el-switch v-model="form.is_dorm_leader" active-text="是" inactive-text="否" />
          </el-form-item>
          <el-form-item v-if="editing" label="学籍状态">
            <el-select v-model="form.status" style="width: 100%">
              <el-option label="在校" value="active" />
              <el-option label="毕业" value="graduated" />
              <el-option label="休学" value="suspended" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importVisible" title="Excel 导入学生" width="520px" destroy-on-close>
      <div class="import-box">
        <div class="import-icon"><el-icon><UploadFilled /></el-icon></div>
        <h3>选择学生名单 Excel</h3>
        <p>表头需包含：学号、姓名、性别、院系编码、班级、手机号、是否舍长。</p>
        <input ref="fileInput" class="hidden-input" type="file" accept=".xlsx" @change="onFileChange" />
        <el-button plain @click="fileInput?.click()">
          <el-icon><FolderOpened /></el-icon>{{ importFile ? importFile.name : '选择 .xlsx 文件' }}
        </el-button>
        <el-button link type="primary" @click="downloadTemplate">下载导入模板</el-button>
      </div>
      <div v-if="importErrors.length" class="import-errors">
        <strong>校验未通过（{{ importErrors.length }} 项）</strong>
        <ul>
          <li v-for="error in importErrors.slice(0, 8)" :key="error">{{ error }}</li>
        </ul>
      </div>
      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" :loading="importing" :disabled="!importFile" @click="doImport">开始导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import PageHeader from '@/components/PageHeader.vue'
import StatusTag from '@/components/StatusTag.vue'
import { departmentApi, excelApi, studentApi } from '@/api'
import { GENDER_LABELS } from '@/utils/constants'
import { getErrorMessage } from '@/api/http'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const canManage = computed(() => ['sys_admin', 'building_admin'].includes(auth.role))
const rows = ref([])
const departments = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const filters = reactive({ keyword: '', department_id: null, status: '' })

const visible = ref(false)
const editing = ref(false)
const saving = ref(false)
const formRef = ref()
const form = reactive({
  id: null,
  student_no: '',
  name: '',
  gender: 'male',
  department_id: null,
  class_name: '',
  phone: '',
  is_dorm_leader: false,
  status: 'active',
})
const rules = {
  student_no: [{ required: true, message: '请输入学号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
}

const importVisible = ref(false)
const importing = ref(false)
const importFile = ref(null)
const importErrors = ref([])
const fileInput = ref()

async function loadDepartments() {
  const { data } = await departmentApi.list()
  departments.value = data
}

async function load() {
  loading.value = true
  try {
    const { data } = await studentApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: filters.keyword || undefined,
      department_id: filters.department_id || undefined,
      status: filters.status || undefined,
    })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = false
  Object.assign(form, {
    id: null,
    student_no: '',
    name: '',
    gender: 'male',
    department_id: departments.value[0]?.id || null,
    class_name: '',
    phone: '',
    is_dorm_leader: false,
    status: 'active',
  })
  visible.value = true
}

function openEdit(row) {
  editing.value = true
  Object.assign(form, {
    id: row.id,
    student_no: row.student_no,
    name: row.name,
    gender: row.gender,
    department_id: row.department_id,
    class_name: row.class_name || '',
    phone: row.phone || '',
    is_dorm_leader: Boolean(row.is_dorm_leader),
    status: row.status,
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
    if (editing.value) {
      await studentApi.update(form.id, {
        name: form.name,
        gender: form.gender,
        department_id: form.department_id,
        class_name: form.class_name || null,
        phone: form.phone || null,
        is_dorm_leader: form.is_dorm_leader,
        status: form.status,
      })
    } else {
      await studentApi.create({
        student_no: form.student_no.trim(),
        name: form.name,
        gender: form.gender,
        department_id: form.department_id,
        class_name: form.class_name || null,
        phone: form.phone || null,
        is_dorm_leader: form.is_dorm_leader,
      })
    }
    ElMessage.success('保存成功')
    visible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function createAccount(row) {
  try {
    await ElMessageBox.confirm(
      `为学生「${row.name}」创建登录账号？用户名默认为学号。`,
      '创建学生账号',
      { type: 'info' },
    )
    const { data } = await studentApi.createAccount(row.id)
    await ElMessageBox.alert(
      `用户名：${data.username}\n初始密码：${data.initial_password}\n\n请复制后告知学生，关闭后无法再次查看。`,
      '账号创建成功',
      { confirmButtonText: '我已保存' },
    )
    await load()
  } catch {
    // 用户取消
  }
}

function downloadTemplate() {
  excelApi.studentsTemplate()
}

function openImport() {
  importFile.value = null
  importErrors.value = []
  importVisible.value = true
}

function onFileChange(event) {
  importFile.value = event.target.files?.[0] || null
  importErrors.value = []
}

async function doImport() {
  if (!importFile.value) return
  importing.value = true
  importErrors.value = []
  try {
    const { data } = await excelApi.importStudents(importFile.value)
    ElMessage.success(`导入成功：${data.success} 名学生`)
    importVisible.value = false
    await load()
  } catch (error) {
    const detail = error?.response?.data?.detail
    importErrors.value = detail?.errors || [getErrorMessage(error)]
  } finally {
    importing.value = false
  }
}

function exportStudents() {
  excelApi.exportStudents()
}

onMounted(async () => {
  await loadDepartments()
  await load()
})
</script>

<style scoped>
.import-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 26px 16px;
  text-align: center;
  background: #f7f7f7;
  border: 1px dashed #cfcfcf;
  border-radius: 3px;
}
.import-icon {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  color: #555555;
  background: transparent;
  border: 1px solid #dedede;
  border-radius: 2px;
  font-size: 20px;
}
.import-box h3 {
  margin: 2px 0 0;
  font-size: 15px;
}
.import-box p {
  max-width: 360px;
  margin: 0;
  color: #64748b;
  font-size: 11px;
  line-height: 1.6;
}
.hidden-input {
  display: none;
}
.import-errors {
  margin-top: 14px;
  padding: 12px;
  color: #b91c1c;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
  font-size: 12px;
}
.import-errors ul {
  max-height: 160px;
  margin: 8px 0 0;
  padding-left: 18px;
  overflow: auto;
  line-height: 1.7;
}
</style>
