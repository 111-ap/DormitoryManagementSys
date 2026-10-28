<template>
  <div class="page-shell">
    <PageHeader
      eyebrow="System"
      title="账号管理"
      subtitle="维护系统登录账号、角色以及楼管/水电工负责的楼栋。"
    >
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>新建账号
      </el-button>
    </PageHeader>

    <div class="panel panel-pad">
      <div class="toolbar">
        <el-input
          v-model="filters.keyword"
          clearable
          placeholder="搜索用户名、姓名或手机号"
          style="width: 260px"
          @keyup.enter="load"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="filters.role" clearable placeholder="全部角色" style="width: 150px" @change="load">
          <el-option v-for="item in ROLE_OPTIONS" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-button @click="load"><el-icon><Refresh /></el-icon>刷新</el-button>
        <div class="toolbar-spacer" />
        <span class="muted">共 {{ total }} 个账号</span>
      </div>

      <el-table v-loading="loading" :data="rows" style="margin-top: 14px">
        <el-table-column prop="username" label="登录名" min-width="120" />
        <el-table-column prop="real_name" label="姓名" min-width="100" />
        <el-table-column label="角色" width="130">
          <template #default="{ row }">
            <el-tag :type="ROLE_TAG_TYPES[row.role]" effect="light" round>{{ ROLE_LABELS[row.role] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="联系电话" min-width="130" />
        <el-table-column prop="email" label="邮箱" min-width="170" show-overflow-tooltip />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <StatusTag :value="row.status" />
          </template>
        </el-table-column>
        <el-table-column label="最后登录" width="170">
          <template #default="{ row }">{{ formatDateTime(row.last_login_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button v-if="['building_admin', 'worker'].includes(row.role)" link type="primary" @click="openBuildings(row)">
              负责楼栋
            </el-button>
            <el-button link type="warning" @click="resetPassword(row)">重置密码</el-button>
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

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑账号' : '新建账号'" width="520px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="form-grid">
          <el-form-item label="登录名" prop="username">
            <el-input v-model="form.username" :disabled="editing" placeholder="登录用户名" />
          </el-form-item>
          <el-form-item label="姓名" prop="real_name">
            <el-input v-model="form.real_name" placeholder="真实姓名" />
          </el-form-item>
          <el-form-item label="角色" prop="role">
            <el-select v-model="form.role" style="width: 100%">
              <el-option v-for="item in ROLE_OPTIONS" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item :label="editing ? '新密码（留空不修改）' : '初始密码'" prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="至少 6 位" />
          </el-form-item>
          <el-form-item label="联系电话">
            <el-input v-model="form.phone" placeholder="手机号" />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="form.email" placeholder="邮箱" />
          </el-form-item>
          <el-form-item v-if="editing" label="账号状态">
            <el-select v-model="form.status" style="width: 100%">
              <el-option label="正常" value="active" />
              <el-option label="停用" value="disabled" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="buildingVisible" title="设置负责楼栋" width="460px" destroy-on-close>
      <p class="muted" style="margin-top: 0">
        {{ buildingUser?.role === 'building_admin' ? '楼管账号只能负责一栋楼。' : '水电工可以负责多栋楼。' }}
      </p>
      <el-select
        v-model="selectedBuildings"
        :multiple="buildingUser?.role !== 'building_admin'"
        :multiple-limit="buildingUser?.role === 'building_admin' ? 1 : 0"
        style="width: 100%"
        placeholder="选择楼栋"
      >
        <el-option v-for="b in buildings" :key="b.id" :label="`${b.name}（${b.code}）`" :value="b.id" />
      </el-select>
      <template #footer>
        <el-button @click="buildingVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveBuildings">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import PageHeader from '@/components/PageHeader.vue'
import StatusTag from '@/components/StatusTag.vue'
import { buildingApi, userApi } from '@/api'
import {
  ROLE_LABELS,
  ROLE_OPTIONS,
  ROLE_TAG_TYPES,
  formatDateTime,
} from '@/utils/constants'

const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const filters = reactive({ keyword: '', role: '' })

const dialogVisible = ref(false)
const editing = ref(false)
const saving = ref(false)
const formRef = ref()
const form = reactive({
  id: null,
  username: '',
  real_name: '',
  role: 'building_admin',
  password: '',
  phone: '',
  email: '',
  status: 'active',
})

const rules = {
  username: [{ required: true, message: '请输入登录名', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  password: [
    {
      validator: (_rule, value, callback) => {
        if (!editing.value && !value) callback(new Error('请输入初始密码'))
        else if (value && value.length < 6) callback(new Error('密码至少 6 位'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
}

const buildingVisible = ref(false)
const buildingUser = ref(null)
const selectedBuildings = ref([])
const buildings = ref([])

async function load() {
  loading.value = true
  try {
    const { data } = await userApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: filters.keyword || undefined,
      role: filters.role || undefined,
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
    username: '',
    real_name: '',
    role: 'building_admin',
    password: '',
    phone: '',
    email: '',
    status: 'active',
  })
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = true
  Object.assign(form, {
    id: row.id,
    username: row.username,
    real_name: row.real_name,
    role: row.role,
    password: '',
    phone: row.phone || '',
    email: row.email || '',
    status: row.status,
  })
  dialogVisible.value = true
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
      const payload = {
        real_name: form.real_name,
        phone: form.phone || null,
        email: form.email || null,
        status: form.status,
      }
      if (form.password) payload.password = form.password
      await userApi.update(form.id, payload)
    } else {
      await userApi.create({
        username: form.username.trim(),
        password: form.password,
        real_name: form.real_name,
        role: form.role,
        phone: form.phone || null,
        email: form.email || null,
      })
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function resetPassword(row) {
  try {
    await ElMessageBox.confirm(
      `确定为「${row.real_name}」生成新的随机密码吗？`,
      '重置密码',
      { type: 'warning' },
    )
  } catch {
    return
  }
  const { data } = await userApi.resetPassword(row.id)
  await ElMessageBox.alert(
    `用户：${data.username}\n新密码：${data.initial_password}\n\n请复制后尽快告知用户，关闭后无法再次查看。`,
    '密码已重置',
    { confirmButtonText: '我已保存' },
  )
}

async function loadBuildings() {
  const { data } = await buildingApi.list({ page_size: 100 })
  buildings.value = data.items || []
}

async function openBuildings(row) {
  await loadBuildings()
  buildingUser.value = row
  selectedBuildings.value = []
  buildingVisible.value = true
}

async function saveBuildings() {
  saving.value = true
  try {
    await userApi.setBuildings(buildingUser.value.id, selectedBuildings.value)
    ElMessage.success('负责楼栋已更新')
    buildingVisible.value = false
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
