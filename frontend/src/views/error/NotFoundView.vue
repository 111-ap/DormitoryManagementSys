<template>
  <div class="error-page">
    <div class="error-code">404</div>
    <h1>页面不存在</h1>
    <p>你访问的页面可能已被移动或删除。</p>
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
  min-height: 70vh;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  background: #f8fafc;
  text-align: center;
}
.error-code {
  color: #111111;
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
}
</style>
