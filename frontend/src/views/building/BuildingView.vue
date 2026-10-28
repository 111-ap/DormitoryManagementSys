<template>
  <div class="page-shell">
    <PageHeader
      eyebrow="Accommodation"
      title="楼栋管理"
      subtitle="查看当前权限范围内的宿舍楼，系统管理员可新增和修改楼栋。"
    >
      <el-button v-if="auth.isAdmin" type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>新建楼栋
      </el-button>
    </PageHeader>

    <div class="panel panel-pad">
      <el-table v-loading="loading" :data="rows">
        <el-table-column prop="code" label="楼栋编码" width="130" />
        <el-table-column prop="name" label="楼栋名称" min-width="160" />
        <el-table-column prop="address" label="地址" min-width="180" />
        <el-table-column prop="floors" label="楼层" width="80" />
        <el-table-column label="性别限制" width="110">
          <template #default="{ row }">
            <el-tag effect="plain" :type="row.gender === 'male' ? 'primary' : row.gender === 'female' ? 'danger' : 'info'">
              {{ ROOM_GENDER_LABELS[row.gender] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><StatusTag :value="row.status" /></template>
        </el-table-column>
        <el-table-column v-if="auth.isAdmin" label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="visible" :title="editing ? '编辑楼栋' : '新建楼栋'" width="540px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="form-grid">
          <el-form-item label="楼栋编码" prop="code">
            <el-input v-model="form.code" placeholder="例如 B01" />
          </el-form-item>
          <el-form-item label="楼栋名称" prop="name">
            <el-input v-model="form.name" placeholder="例如 1号楼" />
          </el-form-item>
          <el-form-item label="地址">
            <el-input v-model="form.address" placeholder="例如 东区" />
          </el-form-item>
          <el-form-item label="楼层数">
            <el-input-number v-model="form.floors" :min="1" :max="100" style="width: 100%" />
          </el-form-item>
          <el-form-item label="性别限制">
            <el-select v-model="form.gender" style="width: 100%">
              <el-option label="男生" value="male" />
              <el-option label="女生" value="female" />
              <el-option label="混合" value="mixed" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.status" style="width: 100%">
              <el-option label="正常" value="active" />
              <el-option label="停用" value="disabled" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PageHeader from '@/components/PageHeader.vue'
import StatusTag from '@/components/StatusTag.vue'
import { buildingApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { ROOM_GENDER_LABELS } from '@/utils/constants'

const auth = useAuthStore()
const rows = ref([])
const loading = ref(false)
const visible = ref(false)
const editing = ref(false)
const saving = ref(false)
const formRef = ref()
const form = reactive({
  id: null,
  code: '',
  name: '',
  address: '',
  floors: 6,
  gender: 'mixed',
  status: 'active',
})
const rules = {
  code: [{ required: true, message: '请输入楼栋编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入楼栋名称', trigger: 'blur' }],
}

async function load() {
  loading.value = true
  try {
    const { data } = await buildingApi.list({ page_size: 100 })
    rows.value = data.items
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = false
  Object.assign(form, { id: null, code: '', name: '', address: '', floors: 6, gender: 'mixed', status: 'active' })
  visible.value = true
}

function openEdit(row) {
  editing.value = true
  Object.assign(form, { ...row, address: row.address || '' })
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
    const payload = { ...form, address: form.address || null }
    if (editing.value) await buildingApi.update(form.id, payload)
    else await buildingApi.create(payload)
    ElMessage.success('保存成功')
    visible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
