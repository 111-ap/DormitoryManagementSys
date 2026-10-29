<template>
  <div class="app-layout" :class="{ 'is-mobile': isMobile, 'mobile-open': mobileOpen }">
    <div v-if="isMobile && mobileOpen" class="sidebar-mask" @click="mobileOpen = false" />
    <aside class="app-sidebar" :class="{ collapsed, 'mobile-visible': mobileOpen }">
      <div class="brand" @click="router.push('/dashboard')">
        <div class="brand-mark"><el-icon><House /></el-icon></div>
        <div v-show="!collapsed" class="brand-text">
          <strong>宿管通</strong>
          <span>宿舍信息管理</span>
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
  background: var(--dms-sidebar);
  color: #e8e8e8;
  border-right: 1px solid #232323;
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
  flex: 0 0 34px;
  width: 34px;
  height: 34px;
  place-items: center;
  color: #111111;
  background: #ffffff;
  border: 1px solid #ffffff;
  border-radius: 2px;
  font-size: 18px;
}
.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}
.brand-text strong {
  color: #ffffff;
  font-size: 16px;
  letter-spacing: 0.02em;
}
.brand-text span {
  margin-top: 3px;
  color: #8a8a8a;
  font-size: 10px;
  letter-spacing: 0.02em;
}
.role-card {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 16px 8px;
  padding: 8px 10px;
  color: #b9b9b9;
  background: transparent;
  border: 1px solid #2c2c2c;
  border-radius: 2px;
  font-size: 11px;
}
.role-dot {
  width: 5px;
  height: 5px;
  background: #d4d4d4;
  border-radius: 50%;
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
  height: 40px;
  margin: 2px 0;
  color: #a3a3a3;
  border-radius: 2px;
  font-size: 12px;
}
.side-menu :deep(.el-menu-item:hover) {
  color: #ffffff;
  background: #1e1e1e;
}
.side-menu :deep(.el-menu-item.is-active) {
  color: #111111;
  background: #ffffff;
  font-weight: 600;
}
.side-menu :deep(.el-menu-item .el-icon) {
  font-size: 16px;
}
.menu-group-title {
  padding: 15px 12px 5px;
  color: #6f6f6f;
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.02em;
}
.sidebar-footer {
  padding: 12px;
  border-top: 1px solid #252525;
}
.collapse-btn {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 10px;
  padding: 9px 11px;
  color: #8a8a8a;
  background: transparent;
  border: 0;
  border-radius: 2px;
  cursor: pointer;
  font-size: 11px;
}
.collapse-btn:hover {
  color: #ffffff;
  background: #1e1e1e;
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
  background: rgba(255, 255, 255, 0.94);
  border-bottom: 1px solid var(--dms-line);
  backdrop-filter: blur(10px);
}
.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}
.header-kicker {
  color: #949494;
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0;
}
.header-title {
  margin-top: 2px;
  color: var(--dms-ink);
  font-size: 17px;
  font-weight: 700;
}
.icon-button {
  display: inline-grid;
  width: 36px;
  height: 36px;
  padding: 0;
  place-items: center;
  color: #555555;
  background: #fff;
  border: 1px solid var(--dms-line);
  border-radius: 3px;
}
.icon-button:hover {
  color: #111111;
  border-color: #a8a8a8;
}
.notification-button {
  padding-top: 5px;
}
.user-chip {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 4px 7px 4px 4px;
  background: #fff;
  border: 1px solid var(--dms-line);
  border-radius: 3px;
  cursor: pointer;
}
.user-chip:hover {
  border-color: #a8a8a8;
}
.avatar {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  color: #fff;
  background: #111111;
  border-radius: 2px;
  font-size: 12px;
  font-weight: 700;
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
