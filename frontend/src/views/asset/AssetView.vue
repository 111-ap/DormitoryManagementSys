<template>
  <div class="page-shell">
    <PageHeader
      eyebrow="Assets"
      title="资产台账"
      subtitle="维护房间内的床铺、柜子、桌椅、电灯等资产，报修单可关联具体资产。"
    >
      <el-button v-if="canManage" type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>新增资产
      </el-button>
    </PageHeader>

    <div class="panel panel-pad">
      <div class="toolbar">
        <el-input v-model="filters.keyword" clearable placeholder="资产编号 / 名称" style="width: 220px" @keyup.enter="load">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="filters.category_id" clearable placeholder="全部类别" style="width: 150px" @change="load">
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-select v-model="filters.status" clearable placeholder="全部状态" style="width: 140px" @change="load">
          <el-option label="正常" value="normal" />
          <el-option label="维修中" value="repairing" />
          <el-option label="报废" value="scrapped" />
          <el-option label="闲置" value="idle" />
        </el-select>
        <el-button @click="load"><el-icon><Refresh /></el-icon>刷新</el-button>
        <div class="toolbar-spacer" />
        <span class="muted">共 {{ total }} 件资产</span>
      </div>

      <el-table v-loading="loading" :data="rows" style="margin-top: 14px">
        <el-table-column prop="asset_no" label="资产编号" min-width="160" />
        <el-table-column prop="name" label="资产名称" min-width="130" />
        <el-table-column prop="category_name" label="类别" width="110" />
        <el-table-column label="位置" min-width="150">
          <template #default="{ row }">{{ row.building_name }} · {{ row.room_no }}</template>
        </el-table-column>
        <el-table-column prop="brand" label="品牌/规格" min-width="120" />
        <el-table-column label="购置日期" width="120">
          <template #default="{ row }">{{ formatDate(row.purchase_date) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><StatusTag :value="row.status" /></template>
        </el-table-column>
        <el-table-column v-if="canManage" label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
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

    <el-dialog v-model="visible" :title="editing ? '编辑资产' : '新增资产'" width="600px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="form-grid">
          <el-form-item label="资产编号" prop="asset_no">
            <el-input v-model="form.asset_no" :disabled="editing" placeholder="例如 B01-101-BED-01" />
          </el-form-item>
          <el-form-item label="资产名称" prop="name">
            <el-input v-model="form.name" placeholder="例如 上下铺" />
          </el-form-item>
          <el-form-item label="资产类别" prop="category_id">
            <el-select v-model="form.category_id" style="width: 100%">
              <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="所属房间" prop="room_id">
            <el-select v-model="form.room_id" filterable style="width: 100%">
              <el-option
                v-for="room in rooms"
                :key="room.id"
                :label="`${room.building_name} · ${room.room_no}`"
                :value="room.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="品牌/规格">
            <el-input v-model="form.brand" placeholder="例如 标准" />
          </el-form-item>
          <el-form-item label="购置日期">
            <el-date-picker v-model="form.purchase_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-form-item v-if="editing" label="状态">
            <el-select v-model="form.status" style="width: 100%">
              <el-option label="正常" value="normal" />
              <el-option label="维修中" value="repairing" />
              <el-option label="报废" value="scrapped" />
              <el-option label="闲置" value="idle" />
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
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PageHeader from '@/components/PageHeader.vue'
import StatusTag from '@/components/StatusTag.vue'
import { assetApi, roomApi } from '@/api'
import { formatDate } from '@/utils/constants'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const canManage = computed(() => ['sys_admin', 'building_admin'].includes(auth.role))
const rows = ref([])
const categories = ref([])
const rooms = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const filters = reactive({ keyword: '', category_id: null, status: '' })

const visible = ref(false)
const editing = ref(false)
const saving = ref(false)
const formRef = ref()
const form = reactive({
  id: null,
  asset_no: '',
  name: '',
  category_id: null,
  room_id: null,
  brand: '',
  purchase_date: null,
  status: 'normal',
})
const rules = {
  asset_no: [{ required: true, message: '请输入资产编号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入资产名称', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择资产类别', trigger: 'change' }],
  room_id: [{ required: true, message: '请选择所属房间', trigger: 'change' }],
}

async function loadOptions() {
  const [categoryRes, roomRes] = await Promise.all([
    assetApi.categories(),
    roomApi.list({ page_size: 100 }),
  ])
  categories.value = categoryRes.data
  rooms.value = roomRes.data.items
}

async function load() {
  loading.value = true
  try {
    const { data } = await assetApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: filters.keyword || undefined,
      category_id: filters.category_id || undefined,
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
    asset_no: '',
    name: '',
    category_id: categories.value[0]?.id || null,
    room_id: rooms.value[0]?.id || null,
    brand: '',
    purchase_date: null,
    status: 'normal',
  })
  visible.value = true
}

function openEdit(row) {
  editing.value = true
  Object.assign(form, {
    id: row.id,
    asset_no: row.asset_no,
    name: row.name,
    category_id: row.category_id,
    room_id: row.room_id,
    brand: row.brand || '',
    purchase_date: row.purchase_date,
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
      await assetApi.update(form.id, {
        name: form.name,
        brand: form.brand || null,
        purchase_date: form.purchase_date || null,
        status: form.status,
      })
    } else {
      await assetApi.create({
        asset_no: form.asset_no.trim(),
        category_id: form.category_id,
        room_id: form.room_id,
        name: form.name,
        brand: form.brand || null,
        purchase_date: form.purchase_date || null,
        status: 'normal',
      })
    }
    ElMessage.success('保存成功')
    visible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadOptions()
  await load()
})
</script>
