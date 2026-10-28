# 前端服务

Vue 3 + Vite + JavaScript + Element Plus + Pinia + Vue Router + ECharts。

## 1. 环境

- Node.js 20.19+ / 当前 Node 24
- 后端 FastAPI 运行在 `http://127.0.0.1:8000`

## 2. 安装与启动

```bash
cd frontend
npm install
npm run dev
```

访问：<http://127.0.0.1:5173>

Vite 会把 `/api` 代理到 `http://127.0.0.1:8000`，所以后端必须同时启动。

## 3. 构建

```bash
npm run build
npm run preview
```

构建产物在 `frontend/dist`，已被 `.gitignore` 忽略。

## 4. 登录

- 管理员账号：`admin`
- 初始密码：项目根目录 `.env` 的 `ADMIN_INITIAL_PASSWORD`
- 学生账号：由管理员在“学生档案 → 创建账号”生成

## 5. 已实现页面

- 登录、工作台
- 账号管理、院系管理
- 楼栋管理、房间信息
- 学生档案、住宿分配、我的宿舍
- 资产台账、报修工单
- 水电账户/账单/充值
- 访客登记、物品出入
- 公告信息、消息通知
- 个人中心、403/404

详细设计见 [前端设计文档](../docs/frontend-design.md)。

## 6. 截图

- 登录页：`docs/screenshots/login.png`
- 工作台：`docs/screenshots/dashboard.png`
- 学生档案：`docs/screenshots/students.png`
- 水电管理：`docs/screenshots/utilities.png`
