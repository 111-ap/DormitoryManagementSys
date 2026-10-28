import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { authApi, studentApi } from '@/api'

const TOKEN_KEY = 'dms_token'
const USER_KEY = 'dms_user'

function readUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref(readUser())
  const student = ref(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => Boolean(token.value))
  const role = computed(() => user.value?.role || '')
  const isAdmin = computed(() => role.value === 'sys_admin')
  const isStaff = computed(() => ['sys_admin', 'building_admin', 'worker'].includes(role.value))
  const isStudent = computed(() => role.value === 'student')
  const isDormLeader = computed(() => Boolean(student.value?.is_dorm_leader))
  const displayName = computed(() => user.value?.real_name || user.value?.username || '未登录')
  const initials = computed(() => displayName.value.slice(0, 1))

  function persist() {
    if (token.value) localStorage.setItem(TOKEN_KEY, token.value)
    else localStorage.removeItem(TOKEN_KEY)
    if (user.value) localStorage.setItem(USER_KEY, JSON.stringify(user.value))
    else localStorage.removeItem(USER_KEY)
  }

  async function login(payload) {
    loading.value = true
    try {
      const { data } = await authApi.login(payload)
      token.value = data.access_token
      user.value = data.user
      persist()
      if (data.user.role === 'student') {
        await fetchStudent()
      }
      return data.user
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!token.value) return null
    const { data } = await authApi.me()
    user.value = data
    persist()
    if (data.role === 'student') await fetchStudent()
    return data
  }

  async function fetchStudent() {
    if (!token.value || role.value !== 'student') {
      student.value = null
      return null
    }
    try {
      const { data } = await studentApi.me()
      student.value = data
      return data
    } catch {
      student.value = null
      return null
    }
  }

  async function ensureLoaded() {
    if (!token.value) return false
    if (user.value) {
      if (role.value === 'student' && !student.value) await fetchStudent()
      return true
    }
    try {
      await fetchMe()
      return true
    } catch {
      logout()
      return false
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    student.value = null
    persist()
  }

  function hasRole(roles) {
    if (!roles || roles.length === 0) return true
    return roles.includes(role.value)
  }

  return {
    token,
    user,
    student,
    loading,
    isAuthenticated,
    role,
    isAdmin,
    isStaff,
    isStudent,
    isDormLeader,
    displayName,
    initials,
    login,
    fetchMe,
    fetchStudent,
    ensureLoaded,
    logout,
    hasRole,
  }
})
