import { createRouter, createWebHistory } from 'vue-router'

import MainLayout from '@/layouts/MainLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { PAGE_TITLES } from './menu'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/login/LoginView.vue'),
    meta: { public: true, title: '登录' },
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
      },
      {
        path: 'users',
        name: 'users',
        component: () => import('@/views/system/UserView.vue'),
        meta: { roles: ['sys_admin'] },
      },
      {
        path: 'departments',
        name: 'departments',
        component: () => import('@/views/system/DepartmentView.vue'),
        meta: { roles: ['sys_admin'] },
      },
      {
        path: 'buildings',
        name: 'buildings',
        component: () => import('@/views/building/BuildingView.vue'),
        meta: { roles: ['sys_admin', 'building_admin', 'worker'] },
      },
      {
        path: 'rooms',
        name: 'rooms',
        component: () => import('@/views/building/RoomView.vue'),
      },
      {
        path: 'students',
        name: 'students',
        component: () => import('@/views/student/StudentView.vue'),
        meta: { roles: ['sys_admin', 'building_admin', 'worker'] },
      },
      {
        path: 'assignments',
        name: 'assignments',
        component: () => import('@/views/student/AssignmentView.vue'),
        meta: { roles: ['sys_admin', 'building_admin'] },
      },
      {
        path: 'my-dorm',
        name: 'my-dorm',
        component: () => import('@/views/student/MyDormView.vue'),
        meta: { roles: ['student'] },
      },
      {
        path: 'assets',
        name: 'assets',
        component: () => import('@/views/asset/AssetView.vue'),
        meta: { roles: ['sys_admin', 'building_admin', 'worker'] },
      },
      {
        path: 'repairs',
        name: 'repairs',
        component: () => import('@/views/repair/RepairView.vue'),
      },
      {
        path: 'utilities',
        name: 'utilities',
        component: () => import('@/views/utility/UtilityView.vue'),
      },
      {
        path: 'visitors',
        name: 'visitors',
        component: () => import('@/views/security/VisitorView.vue'),
      },
      {
        path: 'items',
        name: 'items',
        component: () => import('@/views/security/ItemView.vue'),
      },
      {
        path: 'notices',
        name: 'notices',
        component: () => import('@/views/notice/NoticeView.vue'),
      },
      {
        path: 'notifications',
        name: 'notifications',
        component: () => import('@/views/notice/NotificationView.vue'),
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/profile/ProfileView.vue'),
      },
      {
        path: '403',
        name: 'forbidden',
        component: () => import('@/views/error/ForbiddenView.vue'),
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/error/NotFoundView.vue'),
    meta: { public: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  document.title = `${to.meta.title || PAGE_TITLES[to.path] || '宿舍管理'} · 宿管通`

  if (to.meta.public) {
    if (to.path === '/login' && auth.isAuthenticated) return '/dashboard'
    return true
  }

  if (!auth.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  const loaded = await auth.ensureLoaded()
  if (!loaded) return { path: '/login', query: { redirect: to.fullPath } }

  const roles = to.meta.roles
  if (roles?.length && !roles.includes(auth.role)) {
    return '/403'
  }
  return true
})

export default router
