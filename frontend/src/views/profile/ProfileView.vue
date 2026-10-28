<template>
  <div class="page-shell">
    <PageHeader
      eyebrow="Account"
      title="个人中心"
      subtitle="查看账号信息、学生档案，并修改登录密码。"
    />

    <div class="profile-grid">
      <div class="panel panel-pad profile-card">
        <div class="profile-avatar">{{ auth.initials }}</div>
        <h3>{{ auth.displayName }}</h3>
        <p class="profile-role">{{ ROLE_LABELS[auth.role] }}</p>
        <div class="profile-meta">
          <div><span>登录名</span><strong>{{ auth.user?.username }}</strong></div>
          <div><span>联系电话</span><strong>{{ auth.user?.phone || '—' }}</strong></div>
          <div><span>邮箱</span><strong>{{ auth.user?.email || '—' }}</strong></div>
          <div><span>账号状态</span><StatusTag :value="auth.user?.status || 'active'" /></div>
        </div>
      </div>

      <div class="panel panel-pad">
        <h3 class="section-title">修改密码</h3>
        <p class="section-desc">建议定期更换密码，至少 6 位。</p>
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" style="margin-top: 16px; max-width: 460px">
          <el-form-item label="原密码" prop="old_password">
            <el-input v-model="form.old_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="新密码" prop="new_password">
            <el-input v-model="form.new_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="确认新密码" prop="confirm_password">
            <el-input v-model="form.confirm_password" type="password" show-password />
          </el-form-item>
          <el-button type="primary" :loading="saving" @click="submit">保存新密码</el-button>
        </el-form>
      </div>
    </div>

    <div v-if="auth.isStudent && auth.student" class="panel panel-pad">
      <h3 class="section-title">学生档案</h3>
      <div class="detail-grid" style="margin-top: 16px">
        <div class="detail-item"><div class="label">学号</div><div class="value">{{ auth.student.student_no }}</div></div>
        <div class="detail-item"><div class="label">姓名</div><div class="value">{{ auth.student.name }}</div></div>
        <div class="detail-item"><div class="label">院系</div><div class="value">{{ auth.student.department_name || '—' }}</div></div>
        <div class="detail-item"><div class="label">班级</div><div class="value">{{ auth.student.class_name || '—' }}</div></div>
        <div class="detail-item"><div class="label">当前宿舍</div><div class="value">{{ auth.student.building_name || '未分配' }} {{ auth.student.room_no || '' }}</div></div>
        <div class="detail-item"><div class="label">床位</div><div class="value">{{ auth.student.bed_no || '—' }}</div></div>
        <div class="detail-item"><div class="label">舍长</div><div class="value">{{ auth.student.is_dorm_leader ? '是' : '否' }}</div></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PageHeader from '@/components/PageHeader.vue'
import StatusTag from '@/components/StatusTag.vue'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { ROLE_LABELS } from '@/utils/constants'

const auth = useAuthStore()
const saving = ref(false)
const formRef = ref()
const form = reactive({ old_password: '', new_password: '', confirm_password: '' })
const rules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirm_password: [
    {
      validator: (_rule, value, callback) => {
        if (!value) callback(new Error('请再次输入新密码'))
        else if (value !== form.new_password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
}

async function submit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    await authApi.changePassword({
      old_password: form.old_password,
      new_password: form.new_password,
    })
    ElMessage.success('密码修改成功')
    form.old_password = ''
    form.new_password = ''
    form.confirm_password = ''
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.profile-grid {
  display: grid;
  grid-template-columns: minmax(280px, 0.7fr) minmax(0, 1.3fr);
  gap: 16px;
}
.profile-card {
  text-align: center;
}
.profile-avatar {
  display: grid;
  width: 78px;
  height: 78px;
  margin: 4px auto 14px;
  place-items: center;
  color: #fff;
  background: linear-gradient(135deg, #0f766e, #2dd4bf);
  border-radius: 24px;
  font-size: 30px;
  font-weight: 800;
  box-shadow: 0 14px 28px rgba(15, 118, 110, 0.18);
}
.profile-card h3 {
  margin: 0;
  font-size: 21px;
}
.profile-role {
  margin: 6px 0 18px;
  color: #64748b;
  font-size: 12px;
}
.profile-meta {
  display: flex;
  flex-direction: column;
  gap: 1px;
  text-align: left;
  border-top: 1px solid #f1f5f9;
}
.profile-meta > div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 11px 0;
  border-bottom: 1px solid #f8fafc;
  font-size: 12px;
}
.profile-meta span {
  color: #94a3b8;
}
.profile-meta strong {
  color: #334155;
  font-weight: 600;
}
@media (max-width: 800px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
}
</style>
