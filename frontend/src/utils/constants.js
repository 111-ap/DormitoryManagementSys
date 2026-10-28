export const ROLE_LABELS = {
  sys_admin: '系统管理员',
  building_admin: '宿舍楼管理员',
  worker: '水电工',
  student: '学生',
}

export const ROLE_TAG_TYPES = {
  sys_admin: 'danger',
  building_admin: 'warning',
  worker: 'success',
  student: 'info',
}

export const GENDER_LABELS = {
  male: '男',
  female: '女',
  other: '其他',
  mixed: '不限',
}

export const ROOM_GENDER_LABELS = {
  male: '男生',
  female: '女生',
  mixed: '混合',
}

export const STATUS_LABELS = {
  active: '正常',
  disabled: '停用',
  normal: '正常',
  maintenance: '维修中',
  closed: '关闭',
  graduated: '已毕业',
  suspended: '休学',
  checked_out: '已退宿',
  transferring: '调宿中',
  repairing: '维修中',
  scrapped: '报废',
  idle: '闲置',
  pending: '待处理',
  processing: '处理中',
  completed: '已办结',
  cancelled: '已取消',
  unpaid: '未缴费',
  paid: '已缴费',
  success: '成功',
  failed: '失败',
  visiting: '来访中',
  left: '已离开',
  approved: '已通过',
  rejected: '已驳回',
  published: '已发布',
  archived: '已归档',
}

export const STATUS_TAG_TYPES = {
  active: 'success',
  disabled: 'info',
  normal: 'success',
  maintenance: 'warning',
  closed: 'info',
  graduated: 'info',
  suspended: 'warning',
  checked_out: 'info',
  transferring: 'warning',
  repairing: 'warning',
  scrapped: 'danger',
  idle: 'info',
  pending: 'warning',
  processing: 'primary',
  completed: 'success',
  cancelled: 'info',
  unpaid: 'danger',
  paid: 'success',
  success: 'success',
  failed: 'danger',
  visiting: 'warning',
  left: 'info',
  approved: 'success',
  rejected: 'danger',
  published: 'success',
  archived: 'info',
}

export const PRIORITY_LABELS = {
  low: '低',
  normal: '普通',
  high: '高',
  urgent: '紧急',
}

export const PRIORITY_TAG_TYPES = {
  low: 'info',
  normal: 'primary',
  high: 'warning',
  urgent: 'danger',
}

export const PAY_METHOD_LABELS = {
  wechat_mock: '模拟微信',
  alipay_mock: '模拟支付宝',
  admin_cash: '管理员代充',
}

export const ROLE_OPTIONS = Object.entries(ROLE_LABELS).map(([value, label]) => ({
  value,
  label,
}))

export function labelOf(map, value, fallback = '—') {
  return map[value] || fallback
}

export function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleDateString('zh-CN')
}

export function formatDateTime(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleString('zh-CN', { hour12: false })
}

export function formatMoney(value) {
  if (value === null || value === undefined || value === '') return '¥0.00'
  const num = Number(value)
  if (Number.isNaN(num)) return `¥${value}`
  return `¥${num.toFixed(2)}`
}

export function toNumber(value, fallback = 0) {
  const num = Number(value)
  return Number.isFinite(num) ? num : fallback
}
