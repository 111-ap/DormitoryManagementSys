<template>
  <div class="error-page">
    <div class="error-code">403</div>
    <h1>没有访问权限</h1>
    <p>当前账号没有访问该页面的权限，请联系管理员调整角色或楼栋范围。</p>
    <el-button type="primary" @click="router.replace('/dashboard')">返回工作台</el-button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<style scoped>
.error-page {
  display: flex;
  min-height: 60vh;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  text-align: center;
}
.error-code {
  color: #0f766e;
  font-size: 96px;
  font-weight: 900;
  letter-spacing: -0.08em;
  line-height: 1;
}
.error-page h1 {
  margin: 8px 0;
  font-size: 24px;
}
.error-page p {
  max-width: 420px;
  margin: 0 0 22px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.7;
}
</style>
