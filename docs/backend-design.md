# 后端设计与实现说明

| 项目 | 内容 |
|---|---|
| 技术栈 | Python 3.11 + FastAPI + SQLAlchemy 2 + PyMySQL + MySQL |
| API 前缀 | `/api/v1` |
| 认证方式 | JWT Bearer Token |
| 文档地址 | `http://127.0.0.1:8000/docs` |
| 代码目录 | `backend/app` |
| 启动脚本 | `backend/.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000` |

## 1. 分层结构

```text
backend/
├─ app/
│  ├─ main.py                 # FastAPI 实例、CORS、健康检查
│  ├─ core/
│  │  ├─ config.py            # .env 配置
│  │  ├─ security.py          # bcrypt、JWT
│  │  └─ deps.py              # 当前用户、角色、楼栋权限
│  ├─ db/
│  │  ├─ base.py              # SQLAlchemy Base
│  │  └─ session.py           # Engine、Session
│  ├─ models.py               # 20 张表的 ORM 映射
│  ├─ schemas.py              # Pydantic 请求/响应模型
│  ├─ services/
│  │  ├─ common.py            # 分页、单号、事务提交
│  │  ├─ notifications.py     # 站内通知
│  │  └─ serializers.py       # ORM 到接口响应的组装
│  └─ api/v1/
│     ├─ auth.py
│     ├─ users.py
│     ├─ departments.py
│     ├─ buildings.py
│     ├─ rooms.py
│     ├─ students.py
│     ├─ assignments.py
│     ├─ assets.py
│     ├─ repairs.py
│     ├─ utilities.py
│     ├─ visitors.py
│     ├─ items.py
│     ├─ notices.py
│     ├─ notifications.py
│     └─ dashboard.py
└─ scripts/
   ├─ create_admin.py         # 初始化管理员
   └─ smoke_test.py           # 端到端冒烟测试
```

请求链路：

```text
Vue3 / Axios
  → FastAPI Router
  → 依赖注入（JWT、角色、楼栋范围）
  → Service / SQLAlchemy Session
  → MySQL
```

## 2. 认证与权限

### 登录

- `POST /api/v1/auth/login`：JSON 登录，返回 JWT 和用户信息；
- `POST /api/v1/auth/token`：OAuth2 表单登录，供 Swagger 使用；
- `GET /api/v1/auth/me`：当前用户；
- `POST /api/v1/auth/change-password`：修改自己的密码。

密码使用 bcrypt 哈希，数据库中不保存明文。JWT 载荷包含 `sub`（用户 ID）、`role`、`iat`、`exp`。

### 角色

| 角色 | 代码 |
|---|---|
| 系统管理员 | `sys_admin` |
| 宿舍楼管理员 | `building_admin` |
| 水电工 | `worker` |
| 学生 | `student` |

舍长不是独立角色，是 `students.is_dorm_leader = true`。

### 楼栋数据范围

`building_ids_for_user()` 统一计算：

- 系统管理员：返回 `None`，表示全部楼栋；
- 楼管/水电工：读取 `staff_buildings`；
- 学生：通过当前住宿记录找到所在楼栋；
- 没有住宿记录的学生：空集合。

所有列表和详情接口必须使用该函数过滤，不能只依赖前端隐藏菜单。

## 3. 已实现接口

| 模块 | 主要接口 |
|---|---|
| 认证 | `/auth/login`、`/auth/token`、`/auth/me`、`/auth/change-password` |
| 用户 | `/users`、`/users/{id}`、`/users/{id}/buildings` |
| 院系 | `/departments` |
| 楼栋 | `/buildings`、`/buildings/{id}` |
| 房间 | `/rooms`、`/rooms/{id}` |
| 学生 | `/students`、`/students/me`、`/students/{id}` |
| 住宿 | `/assignments`、`/assignments/me`、分配、调宿、退宿 |
| 资产 | `/assets`、`/assets/categories` |
| 报修 | `/repairs`、接单、办结、取消 |
| 水电 | `/utilities/accounts`、`/utilities/bills`、充值、支付、流水 |
| 访客 | `/visitors`、离开、取消 |
| 物品 | `/items`、`/items/{id}/review` |
| 公告 | `/notices`、归档 |
| 通知 | `/notifications`、未读数、已读 |
| 统计 | `/dashboard` |
| 系统 | `/health`、`/docs`、`/openapi.json` |

## 4. 关键业务实现

### 分房

1. 校验房间存在、当前用户有楼栋权限；
2. 校验学生没有当前住宿；
3. 校验房间状态、性别限制、容量；
4. 校验床位未被占用；
5. 写入 `room_assignments`，生成当前住宿唯一键；
6. 给学生发送站内通知。

数据库层使用 `active_student_id` 和 `active_bed_key` 两个生成列作为最后防线。

### 调宿

在同一个事务中：

1. 关闭旧住宿记录（`status=checked_out`，写 `check_out_at`）；
2. 校验新房间容量、性别、床位；
3. 创建新住宿记录；
4. 发送调宿通知。

### 报修

- 学生只能报修自己当前房间；
- 楼管可代报修；
- 水电工直接接单，状态 `pending → processing → completed`；
- 取消状态 `cancelled`；
- 报修状态变化写入站内通知。

### 水电

- 每个房间一个 `utility_accounts`；
- 创建账单时校验水/电本期读数不小于上期，一个房间每月只能一张；
- 金额由数据库生成列计算；
- 缴费时锁定账户行，余额不足直接拒绝；
- 充值是“创建订单 → 模拟支付 → 加余额 + 写流水”；
- 所有余额变化都写入 `utility_transactions`。

## 5. 当前实现状态

- [x] 项目骨架、配置、数据库会话
- [x] 20 张表 ORM 映射
- [x] JWT 登录、bcrypt、角色依赖
- [x] 楼栋数据范围
- [x] 用户/院系/楼栋/房间/学生/住宿
- [x] 资产/报修
- [x] 水电账户/账单/充值/余额缴费
- [x] 访客/物品/公告/通知
- [x] 首页统计
- [x] 管理员初始化脚本
- [x] 端到端冒烟测试
- [ ] 报修照片/访客证件照上传接口
- [ ] Excel 导入导出
- [ ] 更完整的 pytest 测试集
- [ ] 前端页面联调
- [ ] Docker Compose

## 6. 本地运行

```bash
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Swagger：

```text
http://127.0.0.1:8000/docs
```

管理员初始密码在项目根目录 `.env` 的 `ADMIN_INITIAL_PASSWORD` 中，不要在聊天、代码或 Git 中提交该值。

## 7. 冒烟测试

```bash
cd backend
.venv\Scripts\python.exe scripts\smoke_test.py
```

测试会写入临时用户、学生、住宿、报修、账单等数据。执行后如需恢复干净数据：

```bash
mysql -u root -p < database/reset.sql
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql
cd backend
.venv\Scripts\python.exe scripts\create_admin.py
```
