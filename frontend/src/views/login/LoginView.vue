<template>
  <div class="login-page">
    <section class="login-brand">
      <div class="brand-top">
        <div class="brand-mark"><el-icon><House /></el-icon></div>
        <div>
          <strong>宿管通</strong>
          <span>Dormitory Management System</span>
        </div>
      </div>

      <div class="brand-copy">
        <p class="eyebrow">Campus Living, Organized.</p>
        <h1>让每一间宿舍<br />都有清晰的数字档案</h1>
        <p class="brand-desc">
          覆盖住宿分配、资产报修、水电账单、访客登记和寝室公告的一体化宿舍信息管理平台。
        </p>
      </div>

      <div class="feature-grid">
        <div v-for="item in features" :key="item.title" class="feature-item">
          <div class="feature-icon"><el-icon><component :is="item.icon" /></el-icon></div>
          <div>
            <strong>{{ item.title }}</strong>
            <p>{{ item.desc }}</p>
          </div>
        </div>
      </div>

      <div class="brand-footer">
        <span class="status-dot" />
        系统服务正常
        <span class="dot-separator">·</span>
        高校学生宿舍信息管理系统
      </div>
    </section>

    <section class="login-panel">
      <div class="login-card">
        <div class="mobile-brand">
          <div class="brand-mark"><el-icon><House /></el-icon></div>
          <strong>宿管通</strong>
        </div>
        <p class="eyebrow">Welcome back</p>
        <h2>登录管理后台</h2>
        <p class="login-subtitle">使用管理员分配的账号登录，学生账号可使用学号登录。</p>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          size="large"
          @keyup.enter="submit"
        >
          <el-form-item label="用户名 / 学号" prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名或学号" clearable>
              <template #prefix><el-icon><User /></el-icon></template>
            </el-input>
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              show-password
            >
              <template #prefix><el-icon><Lock /></el-icon></template>
            </el-input>
          </el-form-item>
          <el-button class="login-button" type="primary" size="large" :loading="auth.loading" @click="submit">
            登录系统
            <el-icon class="button-icon"><Right /></el-icon>
          </el-button>
        </el-form>

        <div class="login-tip">
          <el-icon><InfoFilled /></el-icon>
          账号由系统管理员或宿舍楼管理员分配，如忘记密码请联系管理员重置。
        </div>
      </div>

      <p class="copyright">Dormitory Management System · 课程设计项目</p>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const formRef = ref()
const form = reactive({ username: '', password: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名或学号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const features = [
  { icon: 'OfficeBuilding', title: '住宿全景', desc: '楼栋、房间、床位与住宿历史' },
  { icon: 'Tools', title: '报修闭环', desc: '学生报修、水电工接单与办结' },
  { icon: 'Lightning', title: '水电账单', desc: '房间钱包、充值、账单与流水' },
  { icon: 'Lock', title: '角色权限', desc: '按角色和负责楼栋隔离数据' },
]

async function submit() {
  if (auth.loading) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  try {
    await auth.login({ username: form.username.trim(), password: form.password })
    ElMessage.success('登录成功')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard'
    router.replace(redirect)
  } catch {
    // 错误提示由 axios 拦截器统一处理
  }
}
</script>

<style scoped>
.login-page {
  display: grid;
  min-height: 100vh;
  grid-template-columns: minmax(0, 1.12fr) minmax(420px, 0.88fr);
  background: #f8fafc;
}
.login-brand {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 44px 6vw 36px;
  overflow: hidden;
  color: #ecfeff;
  background:
    radial-gradient(circle at 78% 18%, rgba(94, 234, 212, 0.23), transparent 21rem),
    radial-gradient(circle at 8% 92%, rgba(14, 165, 233, 0.16), transparent 22rem),
    linear-gradient(145deg, #071a24 0%, #0b2a33 52%, #0f3f45 100%);
}
.login-brand::before {
  position: absolute;
  top: 20%;
  right: -120px;
  width: 380px;
  height: 380px;
  content: '';
  border: 1px solid rgba(94, 234, 212, 0.16);
  border-radius: 50%;
  box-shadow: 0 0 0 42px rgba(94, 234, 212, 0.035), 0 0 0 88px rgba(94, 234, 212, 0.02);
}
.brand-top {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}
.brand-mark {
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  color: #062a2d;
  background: linear-gradient(135deg, #5eead4, #14b8a6);
  border-radius: 13px;
  font-size: 22px;
  box-shadow: 0 10px 26px rgba(20, 184, 166, 0.24);
}
.brand-top strong {
  display: block;
  font-size: 19px;
  letter-spacing: 0.12em;
}
.brand-top span {
  display: block;
  margin-top: 3px;
  color: #7dd3c7;
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}
.brand-copy {
  position: relative;
  z-index: 1;
  max-width: 620px;
  margin: 54px 0 38px;
}
.brand-copy .eyebrow {
  color: #5eead4;
}
.brand-copy h1 {
  margin: 14px 0 18px;
  color: #f0fdfa;
  font-size: clamp(34px, 4.1vw, 58px);
  font-weight: 850;
  line-height: 1.13;
  letter-spacing: -0.045em;
}
.brand-desc {
  max-width: 500px;
  margin: 0;
  color: #9fc9c8;
  font-size: 14px;
  line-height: 1.8;
}
.feature-grid {
  position: relative;
  z-index: 1;
  display: grid;
  max-width: 680px;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.feature-item {
  display: flex;
  gap: 10px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(153, 246, 228, 0.1);
  border-radius: 13px;
  backdrop-filter: blur(8px);
}
.feature-icon {
  display: grid;
  flex: 0 0 32px;
  width: 32px;
  height: 32px;
  place-items: center;
  color: #5eead4;
  background: rgba(45, 212, 191, 0.1);
  border-radius: 9px;
}
.feature-item strong {
  color: #e6fffb;
  font-size: 12px;
}
.feature-item p {
  margin: 4px 0 0;
  color: #87b7b6;
  font-size: 11px;
  line-height: 1.5;
}
.brand-footer {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 38px;
  color: #6f9e9e;
  font-size: 11px;
}
.status-dot {
  width: 7px;
  height: 7px;
  background: #34d399;
  border-radius: 50%;
  box-shadow: 0 0 0 4px rgba(52, 211, 153, 0.12);
}
.dot-separator {
  color: #3f6265;
}
.login-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 38px clamp(24px, 5vw, 74px);
}
.login-card {
  width: min(100%, 410px);
}
.mobile-brand {
  display: none;
  align-items: center;
  gap: 10px;
  margin-bottom: 26px;
  color: #0f766e;
  font-size: 19px;
  letter-spacing: 0.08em;
}
.login-card h2 {
  margin: 8px 0 0;
  color: #0f172a;
  font-size: 30px;
  letter-spacing: -0.035em;
}
.login-subtitle {
  margin: 10px 0 28px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.7;
}
.login-button {
  width: 100%;
  height: 48px;
  margin-top: 6px;
  border: 0;
  border-radius: 11px;
  font-size: 14px;
  font-weight: 700;
  box-shadow: 0 12px 24px rgba(15, 118, 110, 0.18);
}
.button-icon {
  margin-left: 4px;
}
.login-tip {
  display: flex;
  gap: 8px;
  margin-top: 26px;
  padding: 12px 13px;
  color: #64748b;
  background: #f1f5f9;
  border-radius: 10px;
  font-size: 11px;
  line-height: 1.6;
}
.login-tip .el-icon {
  flex: 0 0 auto;
  margin-top: 2px;
  color: #0f766e;
}
.copyright {
  margin-top: 38px;
  color: #94a3b8;
  font-size: 10px;
  letter-spacing: 0.04em;
}
@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
  }
  .login-brand {
    display: none;
  }
  .login-panel {
    min-height: 100vh;
    background:
      radial-gradient(circle at 10% 0%, rgba(15, 118, 110, 0.1), transparent 22rem),
      #f8fafc;
  }
  .mobile-brand {
    display: flex;
  }
}
</style>
