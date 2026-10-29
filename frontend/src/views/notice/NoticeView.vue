<template>
  <div class="page-shell">
    <PageHeader
      eyebrow="Notice"
      title="公告信息"
      subtitle="楼管发布本楼公告，舍长发布本寝室公告，学生查看与自己相关的通知。"
    >
      <el-button v-if="canPublish" type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>发布公告
      </el-button>
    </PageHeader>

    <div class="panel panel-pad">
      <div class="toolbar">
        <el-select v-model="filters.scope" clearable placeholder="全部范围" style="width: 140px" @change="load">
          <el-option label="楼栋公告" value="building" />
          <el-option label="寝室公告" value="room" />
        </el-select>
        <el-button @click="load"><el-icon><Refresh /></el-icon>刷新</el-button>
        <div class="toolbar-spacer" />
        <span class="muted">共 {{ total }} 条公告</span>
      </div>

      <div v-loading="loading" class="notice-feed">
        <article v-for="notice in rows" :key="notice.id" class="notice-article">
          <div class="notice-article-head">
            <div class="notice-badges">
              <el-tag :type="notice.scope === 'room' ? 'success' : 'info'" effect="plain" size="small">
                {{ notice.scope === 'room' ? '寝室公告' : '楼栋公告' }}
              </el-tag>
              <span>{{ notice.building_name }}<template v-if="notice.room_no"> · {{ notice.room_no }}</template></span>
            </div>
            <el-button
              v-if="notice.author_id === auth.user?.id || auth.isAdmin"
              link
              type="danger"
              @click="archive(notice)"
            >归档</el-button>
          </div>
          <h3>{{ notice.title }}</h3>
          <p>{{ notice.content }}</p>
          <div class="notice-article-footer">
            <span>{{ notice.author_name }}</span>
            <span>{{ formatDateTime(notice.published_at) }}</span>
          </div>
        </article>
        <el-empty v-if="!rows.length && !loading" :image-size="80" description="暂无公告" />
      </div>

      <div class="table-footer">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[5, 10, 20]"
          layout="total, sizes, prev, pager, next"
          background
          @current-change="load"
          @size-change="load"
        />
      </div>
    </div>

    <el-dialog v-model="visible" title="发布公告" width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" maxlength="150" show-word-limit placeholder="公告标题" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="5" maxlength="5000" show-word-limit placeholder="公告内容" />
        </el-form-item>
        <template v-if="auth.isAdmin">
          <el-form-item label="公告范围">
            <el-radio-group v-model="form.scope">
              <el-radio-button value="building">楼栋</el-radio-button>
              <el-radio-button value="room">寝室</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <div class="form-grid">
            <el-form-item label="楼栋">
              <el-select v-model="form.building_id" style="width: 100%" @change="loadRooms">
                <el-option v-for="b in buildings" :key="b.id" :label="b.name" :value="b.id" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="form.scope === 'room'" label="房间">
              <el-select v-model="form.room_id" style="width: 100%">
                <el-option v-for="r in rooms" :key="r.id" :label="r.room_no" :value="r.id" />
              </el-select>
            </el-form-item>
          </div>
        </template>
        <div v-else class="scope-hint">
          <el-icon><InfoFilled /></el-icon>
          {{ auth.isStudent ? '将以舍长身份发布到当前寝室。' : '将以楼管身份发布到本楼栋。' }}
        </div>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import PageHeader from '@/components/PageHeader.vue'
import { buildingApi, noticeApi, roomApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime } from '@/utils/constants'

const auth = useAuthStore()
const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(5)
const loading = ref(false)
const saving = ref(false)
const filters = reactive({ scope: '' })
const visible = ref(false)
const formRef = ref()
const buildings = ref([])
const rooms = ref([])
const form = reactive({
  title: '',
  content: '',
  scope: 'building',
  building_id: null,
  room_id: null,
})
const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
}
const canPublish = computed(
  () => auth.isAdmin || auth.role === 'building_admin' || (auth.isStudent && auth.isDormLeader),
)

async function load() {
  loading.value = true
  try {
    const { data } = await noticeApi.list({
      page: page.value,
      page_size: pageSize.value,
      scope: filters.scope || undefined,
    })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function loadBuildings() {
  if (!auth.isAdmin) return
  const { data } = await buildingApi.list({ page_size: 100 })
  buildings.value = data.items
}

async function loadRooms() {
  if (!auth.isAdmin || !form.building_id) {
    rooms.value = []
    return
  }
  const { data } = await roomApi.list({ building_id: form.building_id, page_size: 100 })
  rooms.value = data.items
}

async function openCreate() {
  Object.assign(form, {
    title: '',
    content: '',
    scope: auth.isAdmin ? 'building' : auth.isStudent ? 'room' : 'building',
    building_id: null,
    room_id: null,
  })
  await loadBuildings()
  if (auth.isAdmin && buildings.value.length) {
    form.building_id = buildings.value[0].id
    await loadRooms()
  }
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
    await noticeApi.create({
      title: form.title,
      content: form.content,
      scope: form.scope,
      building_id: auth.isAdmin ? form.building_id : null,
      room_id: auth.isAdmin && form.scope === 'room' ? form.room_id : null,
    })
    ElMessage.success('公告已发布')
    visible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function archive(notice) {
  try {
    await ElMessageBox.confirm(`确认归档「${notice.title}」？`, '归档公告', { type: 'warning' })
    await noticeApi.archive(notice.id)
    ElMessage.success('已归档')
    await load()
  } catch {
    // 取消
  }
}

onMounted(load)
</script>

<style scoped>
.notice-feed {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 14px;
  min-height: 240px;
}
.notice-article {
  padding: 17px 18px;
  background: #fff;
  border: 1px solid var(--dms-line);
  border-radius: 3px;
  transition: border-color 0.15s ease;
}
.notice-article:hover {
  border-color: #b6b6b6;
}
.notice-article-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.notice-badges {
  display: flex;
  align-items: center;
  gap: 9px;
  color: #999999;
  font-size: 10px;
}
.notice-article h3 {
  margin: 12px 0 7px;
  color: #222222;
  font-size: 15px;
  font-weight: 650;
}
.notice-article p {
  margin: 0;
  color: #666666;
  font-size: 11px;
  line-height: 1.8;
  white-space: pre-wrap;
}
.notice-article-footer {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-top: 14px;
  padding-top: 11px;
  color: #999999;
  border-top: 1px solid #ededed;
  font-size: 9px;
}
.scope-hint {
  display: flex;
  gap: 7px;
  padding: 10px;
  color: #707070;
  background: #f7f7f7;
  border: 1px solid #ececec;
  border-radius: 3px;
  font-size: 10px;
  line-height: 1.6;
}
.scope-hint .el-icon {
  flex: 0 0 auto;
  margin-top: 2px;
  color: #555555;
}
</style>
