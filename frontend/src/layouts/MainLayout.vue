<template>
  <div class="app-layout" :class="{ 'is-mobile': isMobile, 'mobile-open': mobileOpen }">
    <div v-if="isMobile && mobileOpen" class="sidebar-mask" @click="mobileOpen = false" />
    <aside class="app-sidebar" :class="{ collapsed, 'mobile-visible': mobileOpen }">
      <div class="brand" @click="router.push('/dashboard')">
        <div class="brand-mark"><el-icon><House /></el-icon></div>
        <div v-show="!collapsed" class="brand-text">
          <strong>宿管通</strong>
          <span>Dormitory OS</span>
        </div>
      </div>

      <div v-show="!collapsed" class="role-card">
        <span class="role-dot" />
        <span>{{ roleLabel }}</span>
      </div>

      <el-scrollbar class="menu-scroll">
        <el-menu
          :default-active="route.path"
          :collapse="collapsed"
          :collapse-transition="false"
          router
          class="side-menu"
          @select="mobileOpen = false"
        >
          <template v-for="group in menuGroups" :key="group.title">
            <div v-show="!collapsed" class="menu-group-title">{{ group.title }}</div>
            <el-menu-item v-for="item in group.items" :key="item.path" :index="item.path">
              <el-icon><component :is="item.icon" /></el-icon>
              <template #title>{{ item.title }}</template>
            </el-menu-item>
          </template>
        </el-menu>
      </el-scrollbar>

      <div class="sidebar-footer">
        <button class="collapse-btn" type="button" @click="toggleCollapse">
          <el-icon><component :is="collapsed ? 'Expand' : 'Fold'" /></el-icon>
          <span v-show="!collapsed">收起菜单</span>
        </button>
      </div>
    </aside>

    <div class="app-main">
      <header class="app-header">
        <div class="header-left">
          <el-button class="icon-button" text circle @click="toggleSidebar">
            <el-icon :size="19"><Menu /></el-icon>
          </el-button>
          <div>
            <div class="header-kicker">高校学生宿舍信息管理系统</div>
            <div class="header-title">{{ pageTitle }}</div>
          </div>
        </div>

        <div class="header-right">
          <el-tooltip content="消息通知" placement="bottom">
            <button class="icon-button notification-button" type="button" @click="router.push('/notifications')">
              <el-badge :value="unread" :hidden="!unread" :max="99">
                <el-icon :size="19"><Bell /></el-icon>
              </el-badge>
            </button>
          </el-tooltip>

          <el-dropdown trigger="click" @command="handleCommand">
            <button class="user-chip" type="button">
              <span class="avatar">{{ auth.initials }}</span>
              <span class="user-meta">
                <strong>{{ auth.displayName }}</strong>
                <small>{{ roleLabel }}</small>
              </span>
              <el-icon><ArrowDown /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="page-content">
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { notificationApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { ROLE_LABELS } from '@/utils/constants'
import { PAGE_TITLES, menuForRole } from '@/router/menu'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const collapsed = ref(false)
const isMobile = ref(window.innerWidth <= 960)
const mobileOpen = ref(false)
const unread = ref(0)
let unreadTimer = null

const menuGroups = computed(() => menuForRole(auth.role))
const roleLabel = computed(() => ROLE_LABELS[auth.role] || '用户')
const pageTitle = computed(() => route.meta.title || PAGE_TITLES[route.path] || '工作台')

function handleResize() {
  isMobile.value = window.innerWidth <= 960
  if (!isMobile.value) mobileOpen.value = false
}

function toggleCollapse() {
  if (isMobile.value) {
    mobileOpen.value = false
    return
  }
  collapsed.value = !collapsed.value
}

function toggleSidebar() {
  if (isMobile.value) mobileOpen.value = !mobileOpen.value
  else collapsed.value = !collapsed.value
}

async function loadUnread() {
  if (!auth.isAuthenticated) return
  try {
    const { data } = await notificationApi.unreadCount()
    unread.value = data.count || 0
  } catch {
    unread.value = 0
  }
}

async function handleCommand(command) {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    auth.logout()
    router.replace('/login')
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  loadUnread()
  unreadTimer = window.setInterval(loadUnread, 30000)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (unreadTimer) window.clearInterval(unreadTimer)
})
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  background: var(--dms-bg);
}
.app-sidebar {
  position: fixed;
  z-index: 30;
  top: 0;
  bottom: 0;
  left: 0;
  display: flex;
  width: 252px;
  flex-direction: column;
  background:
    radial-gradient(circle at 15% 0%, rgba(45, 212, 191, 0.16), transparent 17rem),
    var(--dms-sidebar);
  color: #e2e8f0;
  transition: width 0.22s ease, transform 0.22s ease;
}
.app-sidebar.collapsed {
  width: 78px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 74px;
  padding: 0 20px;
  cursor: pointer;
}
.brand-mark {
  display: grid;
  flex: 0 0 38px;
  width: 38px;
  height: 38px;
  place-items: center;
  color: #0b1f2a;
  background: linear-gradient(135deg, #5eead4, #14b8a6);
  border-radius: 12px;
  font-size: 20px;
}
.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}
.brand-text strong {
  color: #f0fdfa;
  font-size: 17px;
  letter-spacing: 0.08em;
}
.brand-text span {
  margin-top: 3px;
  color: #7dd3c7;
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}
.role-card {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 16px 8px;
  padding: 9px 11px;
  color: #a7f3d0;
  background: rgba(45, 212, 191, 0.08);
  border: 1px solid rgba(94, 234, 212, 0.12);
  border-radius: 10px;
  font-size: 12px;
}
.role-dot {
  width: 7px;
  height: 7px;
  background: #2dd4bf;
  border-radius: 50%;
  box-shadow: 0 0 0 4px rgba(45, 212, 191, 0.12);
}
.menu-scroll {
  flex: 1;
}
.side-menu {
  padding: 4px 10px 18px;
  background: transparent;
  border-right: 0;
}
.side-menu :deep(.el-menu-item) {
  height: 44px;
  margin: 3px 0;
  color: #b9c9cf;
  border-radius: 10px;
  font-size: 13px;
}
.side-menu :deep(.el-menu-item:hover) {
  color: #f0fdfa;
  background: rgba(45, 212, 191, 0.08);
}
.side-menu :deep(.el-menu-item.is-active) {
  color: #0b1f2a;
  background: linear-gradient(135deg, #5eead4, #2dd4bf);
  font-weight: 700;
}
.side-menu :deep(.el-menu-item .el-icon) {
  font-size: 17px;
}
.menu-group-title {
  padding: 16px 12px 6px;
  color: #66818b;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.16em;
}
.sidebar-footer {
  padding: 12px;
  border-top: 1px solid rgba(148, 163, 184, 0.12);
}
.collapse-btn {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  color: #8fa6ae;
  background: transparent;
  border: 0;
  border-radius: 9px;
  cursor: pointer;
  font-size: 12px;
}
.collapse-btn:hover {
  color: #e2e8f0;
  background: rgba(148, 163, 184, 0.08);
}
.app-main {
  display: flex;
  width: calc(100% - 252px);
  min-width: 0;
  flex: 1;
  flex-direction: column;
  margin-left: 252px;
  transition: margin-left 0.22s ease, width 0.22s ease;
}
.app-sidebar.collapsed + .app-main {
  width: calc(100% - 78px);
  margin-left: 78px;
}
.app-header {
  position: sticky;
  z-index: 20;
  top: 0;
  display: flex;
  height: 74px;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  background: rgba(246, 248, 251, 0.86);
  border-bottom: 1px solid rgba(226, 232, 240, 0.8);
  backdrop-filter: blur(18px);
}
.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}
.header-kicker {
  color: #94a3b8;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.header-title {
  margin-top: 2px;
  color: #0f172a;
  font-size: 18px;
  font-weight: 800;
}
.icon-button {
  display: inline-grid;
  width: 38px;
  height: 38px;
  padding: 0;
  place-items: center;
  color: #475569;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}
.icon-button:hover {
  color: var(--dms-primary);
  border-color: #a7d9d4;
}
.notification-button {
  padding-top: 5px;
}
.user-chip {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 5px 8px 5px 5px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
}
.user-chip:hover {
  border-color: #a7d9d4;
}
.avatar {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  color: #fff;
  background: linear-gradient(135deg, #0f766e, #14b8a6);
  border-radius: 9px;
  font-size: 14px;
  font-weight: 800;
}
.user-meta {
  display: flex;
  flex-direction: column;
  min-width: 82px;
  text-align: left;
  line-height: 1.15;
}
.user-meta strong {
  overflow: hidden;
  max-width: 120px;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
}
.user-meta small {
  margin-top: 3px;
  color: #94a3b8;
  font-size: 10px;
}
.page-content {
  width: 100%;
  max-width: 1500px;
  margin: 0 auto;
  padding: 24px 28px 44px;
}
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(5px);
}
.sidebar-mask {
  position: fixed;
  z-index: 25;
  inset: 0;
  background: rgba(15, 23, 42, 0.42);
}
@media (max-width: 960px) {
  .app-sidebar {
    transform: translateX(-100%);
  }
  .app-sidebar.mobile-visible {
    transform: translateX(0);
  }
  .app-sidebar.collapsed {
    width: 252px;
  }
  .app-main,
  .app-sidebar.collapsed + .app-main {
    width: 100%;
    margin-left: 0;
  }
  .app-header {
    height: 66px;
    padding: 0 16px;
  }
  .header-kicker,
  .user-meta {
    display: none;
  }
  .page-content {
    padding: 18px 16px 34px;
  }
}
</style>
