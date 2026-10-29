<template>
  <div class="login-page">
    <section class="login-brand">
      <div class="brand-top">
        <div class="brand-mark"><el-icon><House /></el-icon></div>
        <div>
          <strong>宿管通</strong>
          <span>高校学生宿舍信息管理系统</span>
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
  grid-template-columns: minmax(0, 1.08fr) minmax(420px, 0.92fr);
  background: #f4f5f6;
}
.login-brand {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 44px 6vw 36px;
  overflow: hidden;
  color: #f5f5f5;
  background: #111111;
  border-right: 1px solid #242424;
}
.login-brand::before {
  display: none;
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
  width: 38px;
  height: 38px;
  place-items: center;
  color: #111111;
  background: #ffffff;
  border: 1px solid #ffffff;
  border-radius: 2px;
  font-size: 19px;
  box-shadow: none;
}
.brand-top strong {
  display: block;
  color: #ffffff;
  font-size: 17px;
  font-weight: 600;
  letter-spacing: 0.04em;
}
.brand-top span {
  display: block;
  margin-top: 4px;
  color: #999999;
  font-size: 10px;
  letter-spacing: 0.02em;
}
.brand-copy {
  position: relative;
  z-index: 1;
  max-width: 620px;
  margin: 48px 0 34px;
}
.brand-copy .eyebrow {
  display: none;
}
.brand-copy h1 {
  margin: 0 0 20px;
  color: #f7f7f7;
  font-size: clamp(34px, 4.2vw, 58px);
  font-weight: 650;
  line-height: 1.12;
  letter-spacing: -0.05em;
}
.brand-desc {
  max-width: 470px;
  margin: 0;
  color: #a3a3a3;
  font-size: 13px;
  line-height: 1.8;
}
.feature-grid {
  position: relative;
  z-index: 1;
  display: grid;
  max-width: 660px;
  grid-template-columns: 1fr 1fr;
  gap: 0 24px;
  border-top: 1px solid #2b2b2b;
}
.feature-item {
  display: flex;
  gap: 10px;
  padding: 14px 0;
  background: transparent;
  border: 0;
  border-bottom: 1px solid #2b2b2b;
  border-radius: 0;
  backdrop-filter: none;
}
.feature-icon {
  flex: 0 0 24px;
  width: 24px;
  height: 24px;
  padding-top: 1px;
  color: #d4d4d4;
  background: transparent;
  border-radius: 0;
  font-size: 15px;
}
.feature-item strong {
  color: #dedede;
  font-size: 11px;
  font-weight: 600;
}
.feature-item p {
  margin: 4px 0 0;
  color: #8f8f8f;
  font-size: 10px;
  line-height: 1.5;
}
.brand-footer {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 34px;
  color: #7a7a7a;
  font-size: 10px;
}
.status-dot {
  width: 5px;
  height: 5px;
  background: #d4d4d4;
  border-radius: 50%;
  box-shadow: none;
}
.dot-separator {
  color: #454545;
}
.login-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 38px clamp(24px, 5vw, 74px);
  background: #ffffff;
}
.login-card {
  width: min(100%, 390px);
}
.mobile-brand {
  display: none;
  align-items: center;
  gap: 10px;
  margin-bottom: 30px;
  color: #111111;
  font-size: 18px;
  letter-spacing: 0.02em;
}
.mobile-brand .brand-mark {
  color: #ffffff;
  background: #111111;
  border-color: #111111;
}
.login-card h2 {
  margin: 0;
  color: #111111;
  font-size: 30px;
  font-weight: 650;
  letter-spacing: -0.04em;
}
.login-subtitle {
  margin: 10px 0 28px;
  color: #777777;
  font-size: 12px;
  line-height: 1.7;
}
.login-button {
  width: 100%;
  height: 46px;
  margin-top: 8px;
  border: 0;
  border-radius: 3px;
  font-size: 13px;
  font-weight: 600;
  box-shadow: none;
}
.button-icon {
  margin-left: 4px;
}
.login-tip {
  display: flex;
  gap: 8px;
  margin-top: 26px;
  padding: 12px 13px;
  color: #707070;
  background: #f6f6f6;
  border: 1px solid #ececec;
  border-radius: 3px;
  font-size: 10px;
  line-height: 1.6;
}
.login-tip .el-icon {
  flex: 0 0 auto;
  margin-top: 2px;
  color: #555555;
}
.copyright {
  margin-top: 38px;
  color: #9a9a9a;
  font-size: 10px;
  letter-spacing: 0.02em;
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
    background: #f4f5f6;
  }
  .login-card {
    padding: 30px 26px;
    background: #ffffff;
    border: 1px solid #e5e5e5;
    border-radius: 4px;
  }
  .mobile-brand {
    display: flex;
  }
}
</style>
