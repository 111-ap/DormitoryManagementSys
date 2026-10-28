import http, { downloadFile } from './http'

export const authApi = {
  login: (payload) => http.post('/auth/login', payload),
  me: () => http.get('/auth/me'),
  changePassword: (payload) => http.post('/auth/change-password', payload),
}

export const dashboardApi = {
  get: () => http.get('/dashboard'),
}

export const userApi = {
  list: (params) => http.get('/users', { params }),
  create: (payload) => http.post('/users', payload),
  update: (id, payload) => http.patch(`/users/${id}`, payload),
  setBuildings: (id, buildingIds) =>
    http.put(`/users/${id}/buildings`, { building_ids: buildingIds }),
  resetPassword: (id, password = null) =>
    http.post(`/users/${id}/reset-password`, { password }),
}

export const departmentApi = {
  list: () => http.get('/departments'),
  create: (payload) => http.post('/departments', payload),
  update: (id, payload) => http.patch(`/departments/${id}`, payload),
}

export const buildingApi = {
  list: (params) => http.get('/buildings', { params }),
  get: (id) => http.get(`/buildings/${id}`),
  create: (payload) => http.post('/buildings', payload),
  update: (id, payload) => http.patch(`/buildings/${id}`, payload),
}

export const roomApi = {
  list: (params) => http.get('/rooms', { params }),
  get: (id) => http.get(`/rooms/${id}`),
  create: (payload) => http.post('/rooms', payload),
  update: (id, payload) => http.patch(`/rooms/${id}`, payload),
}

export const studentApi = {
  list: (params) => http.get('/students', { params }),
  me: () => http.get('/students/me'),
  get: (id) => http.get(`/students/${id}`),
  create: (payload) => http.post('/students', payload),
  update: (id, payload) => http.patch(`/students/${id}`, payload),
  createAccount: (id, password = null) =>
    http.post(`/students/${id}/account`, { password }),
}

export const assignmentApi = {
  list: (params) => http.get('/assignments', { params }),
  me: () => http.get('/assignments/me'),
  create: (payload) => http.post('/assignments', payload),
  transfer: (id, payload) => http.post(`/assignments/${id}/transfer`, payload),
  checkout: (id) => http.post(`/assignments/${id}/checkout`),
}

export const assetApi = {
  categories: () => http.get('/assets/categories'),
  createCategory: (payload) => http.post('/assets/categories', payload),
  list: (params) => http.get('/assets', { params }),
  get: (id) => http.get(`/assets/${id}`),
  create: (payload) => http.post('/assets', payload),
  update: (id, payload) => http.patch(`/assets/${id}`, payload),
}

export const repairApi = {
  list: (params) => http.get('/repairs', { params }),
  get: (id) => http.get(`/repairs/${id}`),
  create: (payload) => http.post('/repairs', payload),
  accept: (id) => http.post(`/repairs/${id}/accept`, {}),
  complete: (id, payload) => http.post(`/repairs/${id}/complete`, payload),
  cancel: (id, payload) => http.post(`/repairs/${id}/cancel`, payload),
}

export const utilityApi = {
  accounts: (params) => http.get('/utilities/accounts', { params }),
  ensureAccount: (roomId) => http.post(`/utilities/accounts/room/${roomId}`),
  transactions: (accountId, params) =>
    http.get(`/utilities/accounts/${accountId}/transactions`, { params }),
  bills: (params) => http.get('/utilities/bills', { params }),
  createBill: (payload) => http.post('/utilities/bills', payload),
  payBill: (id) => http.post(`/utilities/bills/${id}/pay`),
  recharges: (params) => http.get('/utilities/recharges', { params }),
  createRecharge: (payload) => http.post('/utilities/recharges', payload),
  payRecharge: (id) => http.post(`/utilities/recharges/${id}/pay`),
}

export const visitorApi = {
  list: (params) => http.get('/visitors', { params }),
  create: (payload) => http.post('/visitors', payload),
  leave: (id) => http.post(`/visitors/${id}/leave`),
  cancel: (id) => http.post(`/visitors/${id}/cancel`),
}

export const itemApi = {
  list: (params) => http.get('/items', { params }),
  create: (payload) => http.post('/items', payload),
  review: (id, payload) => http.post(`/items/${id}/review`, payload),
}

export const noticeApi = {
  list: (params) => http.get('/notices', { params }),
  create: (payload) => http.post('/notices', payload),
  archive: (id) => http.post(`/notices/${id}/archive`),
}

export const notificationApi = {
  list: (params) => http.get('/notifications', { params }),
  unreadCount: () => http.get('/notifications/unread-count'),
  read: (id) => http.post(`/notifications/${id}/read`),
  readAll: () => http.post('/notifications/read-all'),
}

export const attachmentApi = {
  list: (bizType, bizId) =>
    http.get('/attachments', { params: { biz_type: bizType, biz_id: bizId } }),
  upload: (bizType, bizId, file) => {
    const form = new FormData()
    form.append('biz_type', bizType)
    form.append('biz_id', String(bizId))
    form.append('file', file)
    return http.post('/attachments/upload', form, { timeout: 60000 })
  },
  remove: (id) => http.delete(`/attachments/${id}`),
  download: (id, filename = 'attachment') =>
    downloadFile(`/attachments/${id}`, null, filename),
}

export const excelApi = {
  studentsTemplate: () =>
    downloadFile('/excel/templates/students', null, 'students_template.xlsx'),
  assignmentsTemplate: () =>
    downloadFile('/excel/templates/assignments', null, 'assignments_template.xlsx'),
  importStudents: (file) => {
    const form = new FormData()
    form.append('file', file)
    return http.post('/excel/import/students', form, { timeout: 60000 })
  },
  importAssignments: (file) => {
    const form = new FormData()
    form.append('file', file)
    return http.post('/excel/import/assignments', form, { timeout: 60000 })
  },
  exportStudents: () => downloadFile('/excel/export/students', null, 'students.xlsx'),
  exportAssignments: () => downloadFile('/excel/export/assignments', null, 'assignments.xlsx'),
  exportRepairs: () => downloadFile('/excel/export/repairs', null, 'repairs.xlsx'),
  exportBills: () => downloadFile('/excel/export/utility-bills', null, 'utility_bills.xlsx'),
  exportVisitors: () => downloadFile('/excel/export/visitors', null, 'visitors.xlsx'),
}
