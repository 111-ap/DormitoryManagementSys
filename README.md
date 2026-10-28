# 高校学生宿舍信息管理系统

软件工程课程设计项目，目标是实现一个前后端分离的宿舍信息管理系统（MIS），覆盖学生住宿、楼栋房间、资产报修、水电费、访客登记、物品出入和公告通知等业务。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + JavaScript + Vue Router + Pinia + Element Plus + Axios + ECharts |
| 后端 | Python 3.11 + FastAPI + SQLAlchemy + Pydantic |
| 数据库 | MySQL 8.0+ / 当前环境 MySQL 26.10 |
| 部署 | 本地 MySQL 优先，后期补 Docker Compose |
| 版本控制 | Git + GitHub |

## 当前进度

- [x] 需求梳理与角色/权限设计
- [x] 数据库设计：20 张表 + 2 个查询视图
- [x] MySQL 建库、建表、演示数据
- [x] 数据库专用账号 `dorm_app`
- [x] 后端项目骨架、JWT 登录、角色与楼栋权限
- [x] 用户/院系/楼栋/房间/学生/住宿接口
- [x] 资产/报修/水电/访客/物品/公告/通知/统计接口
- [x] 管理员初始化脚本与端到端冒烟测试
- [x] 报修照片、访客证件照上传与鉴权下载
- [x] Excel 学生/宿舍分配导入、多类导出
- [x] 学生账号创建、管理员重置密码
- [ ] 前端项目骨架与页面
- [ ] 完整统计图表
- [ ] Docker 部署

## 目录结构

```text
DormitoryManagementSys/
├─ backend/
│  ├─ app/                 # FastAPI 应用
│  │  ├─ core/             # 配置、JWT、权限依赖
│  │  ├─ db/               # SQLAlchemy 会话
│  │  ├─ models.py         # 20 张表 ORM
│  │  ├─ schemas.py        # Pydantic 模型
│  │  ├─ services/         # 分页、通知、序列化
│  │  └─ api/v1/           # 业务路由
│  ├─ scripts/             # 建管理员、冒烟测试
│  ├─ requirements.txt
│  └─ README.md
├─ database/
│  ├─ schema.sql           # 建库、建表、视图
│  ├─ seed.sql             # 院系/楼栋/房间/资产类别等演示数据
│  ├─ reset.sql            # 开发环境重置（会删除数据）
│  └─ README.md
├─ docs/
│  ├─ database-design.md   # 数据库设计说明书
│  ├─ backend-design.md    # 后端架构与接口说明
│  ├─ design-change-log.md # 与最初 ER/DFD 的差异记录
│  └─ reference/           # 需求草图、ER/DFD 参考图片
├─ .env.example            # 环境变量模板
├─ .gitignore
└─ README.md
```

## 数据库

数据库名：`dormitory_db`  
字符集：`utf8mb4` / `utf8mb4_0900_ai_ci`  
应用账号：`dorm_app`，只授权 `dormitory_db.*`

初始化：

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql
```

重置开发库：

```bash
mysql -u root -p < database/reset.sql
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql
```

`reset.sql` 会删除所有业务表和数据，仅用于本地开发。

本地连接信息保存在 `.env`，该文件已被 `.gitignore` 忽略，不要提交到 GitHub。

## 后端运行

```bash
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
.venv\Scripts\python.exe scripts\create_admin.py
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/api/v1/health>
- 管理员账号与初始密码在 `.env` 的 `ADMIN_USERNAME`、`ADMIN_INITIAL_PASSWORD` 中

## 说明

- 详细表结构、字段说明、状态机和权限矩阵见 [数据库设计文档](docs/database-design.md)。
- 后端分层、认证流程和接口列表见 [后端设计文档](docs/backend-design.md)。
- 当前仓库为公开仓库，禁止提交 `.env`、数据库密码、JWT 密钥、真实学生信息和访客证件照。
- 登录账号不预置在种子数据中，后续由后端初始化脚本创建，避免在公开仓库中存放默认密码。
