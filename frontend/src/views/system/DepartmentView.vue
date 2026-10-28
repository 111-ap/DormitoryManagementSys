<template>
  <div class="page-shell">
    <PageHeader
      eyebrow="Organization"
      title="院系管理"
      subtitle="维护学生所属院系，学生档案和统计会引用这里的数据。"
    >
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>新建院系
      </el-button>
    </PageHeader>

    <div class="panel panel-pad">
      <el-table v-loading="loading" :data="rows">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="code" label="院系编码" width="160" />
        <el-table-column prop="name" label="院系名称" min-width="220" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }"><StatusTag :value="row.status" /></template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="visible" :title="editing ? '编辑院系' : '新建院系'" width="420px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="院系编码" prop="code">
          <el-input v-model="form.code" placeholder="例如 CS" />
        </el-form-item>
        <el-form-item label="院系名称" prop="name">
          <el-input v-model="form.name" placeholder="例如 计算机科学与技术学院" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="正常" value="active" />
            <el-option label="停用" value="disabled" />
          </el-select>
        </el-form-item>
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
import { departmentApi } from '@/api'

const rows = ref([])
const loading = ref(false)
const visible = ref(false)
const editing = ref(false)
const saving = ref(false)
const formRef = ref()
const form = reactive({ id: null, code: '', name: '', status: 'active' })
const rules = {
  code: [{ required: true, message: '请输入院系编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入院系名称', trigger: 'blur' }],
}

async function load() {
  loading.value = true
  try {
    const { data } = await departmentApi.list()
    rows.value = data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = false
  Object.assign(form, { id: null, code: '', name: '', status: 'active' })
  visible.value = true
}

function openEdit(row) {
  editing.value = true
  Object.assign(form, { ...row })
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
    if (editing.value) await departmentApi.update(form.id, { code: form.code, name: form.name, status: form.status })
    else await departmentApi.create({ code: form.code, name: form.name, status: form.status })
    ElMessage.success('保存成功')
    visible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
