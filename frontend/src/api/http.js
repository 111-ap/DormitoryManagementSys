import axios from 'axios'
import { ElMessage } from 'element-plus'

const TOKEN_KEY = 'dms_token'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 20000,
})

export function getErrorMessage(error) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || item.message || String(item)).join('；')
  }
  if (detail?.errors) return detail.errors.join('；')
  if (detail?.message) return detail.message
  return error?.message || '请求失败，请稍后重试'
}

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    if (status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem('dms_user')
      if (window.location.pathname !== '/login') {
        window.location.assign('/login')
      }
    }
    if (!error.config?.skipErrorMessage) {
      ElMessage.error(getErrorMessage(error))
    }
    return Promise.reject(error)
  },
)

export async function downloadFile(url, params, fallbackName = 'download.xlsx') {
  const response = await http.get(url, {
    params,
    responseType: 'blob',
    timeout: 60000,
    skipErrorMessage: true,
  })
  const disposition = response.headers['content-disposition'] || ''
  const match = disposition.match(/filename="?([^";]+)"?/i)
  const filename = match?.[1] || fallbackName
  const blob = new Blob([response.data])
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(link.href)
}

export default http
