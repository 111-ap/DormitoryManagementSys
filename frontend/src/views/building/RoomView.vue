<template>
  <div class="page-shell">
    <PageHeader
      eyebrow="Accommodation"
      title="房间信息"
      subtitle="查询楼栋、房间电话、容量和空床位；学生可查看本楼房间电话。"
    >
      <el-button v-if="canManage" type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>新建房间
      </el-button>
    </PageHeader>

    <div class="panel panel-pad">
      <div class="toolbar">
        <el-select v-model="filters.building_id" clearable placeholder="全部楼栋" style="width: 160px" @change="load">
          <el-option v-for="b in buildings" :key="b.id" :label="b.name" :value="b.id" />
        </el-select>
        <el-input v-model="filters.keyword" clearable placeholder="房间号 / 电话" style="width: 220px" @keyup.enter="load">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="filters.status" clearable placeholder="全部状态" style="width: 140px" @change="load">
          <el-option label="正常" value="normal" />
          <el-option label="维修中" value="maintenance" />
          <el-option label="关闭" value="closed" />
        </el-select>
        <el-button @click="load"><el-icon><Refresh /></el-icon>刷新</el-button>
        <div class="toolbar-spacer" />
        <span class="muted">共 {{ total }} 个房间</span>
      </div>

      <el-table v-loading="loading" :data="rows" style="margin-top: 14px">
        <el-table-column prop="building_name" label="楼栋" min-width="110" />
        <el-table-column prop="room_no" label="房间号" width="100" />
        <el-table-column prop="floor" label="楼层" width="75" />
        <el-table-column prop="phone" label="房间电话" min-width="140" />
        <el-table-column label="入住 / 容量" width="125">
          <template #default="{ row }">
            <span class="mono">{{ row.occupied_count || 0 }} / {{ row.capacity }}</span>
          </template>
        </el-table-column>
        <el-table-column label="空床位" width="95">
          <template #default="{ row }">
            <el-tag :type="row.available_beds > 0 ? 'success' : 'info'" effect="plain">
              {{ row.available_beds ?? 0 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="性别" width="90">
          <template #default="{ row }">{{ ROOM_GENDER_LABELS[row.gender] }}</template>
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

    <el-dialog v-model="visible" :title="editing ? '编辑房间' : '新建房间'" width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="form-grid">
          <el-form-item label="所属楼栋" prop="building_id">
            <el-select v-model="form.building_id" style="width: 100%" :disabled="auth.role === 'building_admin'">
              <el-option v-for="b in buildings" :key="b.id" :label="`${b.name}（${b.code}）`" :value="b.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="房间号" prop="room_no">
            <el-input v-model="form.room_no" placeholder="例如 101" />
          </el-form-item>
          <el-form-item label="楼层" prop="floor">
            <el-input-number v-model="form.floor" :min="1" :max="100" style="width: 100%" />
          </el-form-item>
          <el-form-item label="房间电话">
            <el-input v-model="form.phone" placeholder="例如 010-0000-0101" />
          </el-form-item>
          <el-form-item label="可住人数">
            <el-input-number v-model="form.capacity" :min="1" :max="20" style="width: 100%" />
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
              <el-option label="正常" value="normal" />
              <el-option label="维修中" value="maintenance" />
              <el-option label="关闭" value="closed" />
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
import { buildingApi, roomApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { ROOM_GENDER_LABELS } from '@/utils/constants'

const auth = useAuthStore()
const canManage = computed(() => ['sys_admin', 'building_admin'].includes(auth.role))
const buildings = ref([])
const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const filters = reactive({ building_id: null, keyword: '', status: '' })

const visible = ref(false)
const editing = ref(false)
const saving = ref(false)
const formRef = ref()
const form = reactive({
  id: null,
  building_id: null,
  room_no: '',
  floor: 1,
  phone: '',
  capacity: 4,
  gender: 'mixed',
  status: 'normal',
})
const rules = {
  building_id: [{ required: true, message: '请选择楼栋', trigger: 'change' }],
  room_no: [{ required: true, message: '请输入房间号', trigger: 'blur' }],
  floor: [{ required: true, message: '请输入楼层', trigger: 'blur' }],
}

async function loadBuildings() {
  const { data } = await buildingApi.list({ page_size: 100 })
  buildings.value = data.items
  if (!form.building_id && buildings.value.length === 1) form.building_id = buildings.value[0].id
}

async function load() {
  loading.value = true
  try {
    const { data } = await roomApi.list({
      page: page.value,
      page_size: pageSize.value,
      building_id: filters.building_id || undefined,
      keyword: filters.keyword || undefined,
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
    building_id: buildings.value[0]?.id || null,
    room_no: '',
    floor: 1,
    phone: '',
    capacity: 4,
    gender: 'mixed',
    status: 'normal',
  })
  visible.value = true
}

function openEdit(row) {
  editing.value = true
  Object.assign(form, {
    id: row.id,
    building_id: row.building_id,
    room_no: row.room_no,
    floor: row.floor,
    phone: row.phone || '',
    capacity: row.capacity,
    gender: row.gender,
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
    const payload = {
      building_id: form.building_id,
      room_no: form.room_no,
      floor: form.floor,
      phone: form.phone || null,
      capacity: form.capacity,
      gender: form.gender,
      status: form.status,
    }
    if (editing.value) {
      delete payload.building_id
      delete payload.room_no
      await roomApi.update(form.id, payload)
    } else {
      await roomApi.create(payload)
    }
    ElMessage.success('保存成功')
    visible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadBuildings()
  await load()
})
</script>
