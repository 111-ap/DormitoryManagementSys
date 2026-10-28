export const MENU_GROUPS = [
  {
    title: '概览',
    items: [{ path: '/dashboard', title: '工作台', icon: 'Odometer', roles: [] }],
  },
  {
    title: '住宿管理',
    items: [
      {
        path: '/buildings',
        title: '楼栋管理',
        icon: 'OfficeBuilding',
        roles: ['sys_admin', 'building_admin', 'worker'],
      },
      { path: '/rooms', title: '房间信息', icon: 'House', roles: [] },
      {
        path: '/students',
        title: '学生档案',
        icon: 'UserFilled',
        roles: ['sys_admin', 'building_admin', 'worker'],
      },
      {
        path: '/assignments',
        title: '住宿分配',
        icon: 'Connection',
        roles: ['sys_admin', 'building_admin'],
      },
      {
        path: '/my-dorm',
        title: '我的宿舍',
        icon: 'HomeFilled',
        roles: ['student'],
      },
    ],
  },
  {
    title: '资产与报修',
    items: [
      {
        path: '/assets',
        title: '资产台账',
        icon: 'Box',
        roles: ['sys_admin', 'building_admin', 'worker'],
      },
      { path: '/repairs', title: '报修工单', icon: 'Tools', roles: [] },
    ],
  },
  {
    title: '水电与安全',
    items: [
      { path: '/utilities', title: '水电管理', icon: 'Lightning', roles: [] },
      { path: '/visitors', title: '访客登记', icon: 'Postcard', roles: [] },
      { path: '/items', title: '物品出入', icon: 'Suitcase', roles: [] },
      { path: '/notices', title: '公告信息', icon: 'ChatDotSquare', roles: [] },
    ],
  },
  {
    title: '系统管理',
    items: [
      { path: '/users', title: '账号管理', icon: 'User', roles: ['sys_admin'] },
      { path: '/departments', title: '院系管理', icon: 'School', roles: ['sys_admin'] },
    ],
  },
]

export function menuForRole(role) {
  return MENU_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => !item.roles?.length || item.roles.includes(role)),
  })).filter((group) => group.items.length > 0)
}

export const PAGE_TITLES = {
  '/dashboard': '工作台',
  '/users': '账号管理',
  '/departments': '院系管理',
  '/buildings': '楼栋管理',
  '/rooms': '房间信息',
  '/students': '学生档案',
  '/assignments': '住宿分配',
  '/my-dorm': '我的宿舍',
  '/assets': '资产台账',
  '/repairs': '报修工单',
  '/utilities': '水电管理',
  '/visitors': '访客登记',
  '/items': '物品出入',
  '/notices': '公告信息',
  '/notifications': '消息通知',
  '/profile': '个人中心',
}
