# 高校学生宿舍信息管理系统

软件工程课程设计项目，目标是实现一个前后端分离的宿舍信息管理系统（MIS），覆盖学生住宿、楼栋房间、资产报修、水电费、访客登记、物品出入和公告通知等业务。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + JavaScript + Vue Router + Pinia + Element Plus + Axios + ECharts |
| 后端 | Python 3.11 + FastAPI（计划）+ SQLAlchemy + Pydantic |
| 数据库 | MySQL 8.0+ / 当前环境 MySQL 26.10 |
| 部署 | 本地 MySQL 优先，后期补 Docker Compose |
| 版本控制 | Git + GitHub |

## 当前进度

- [x] 需求梳理与角色/权限设计
- [x] 数据库设计：20 张表 + 2 个查询视图
- [x] MySQL 建库、建表、演示数据
- [x] 数据库专用账号 `dorm_app`
- [ ] 后端项目骨架与接口
- [ ] 前端项目骨架与页面
- [ ] Excel 导入导出、照片、通知、统计图
- [ ] Docker 部署

## 目录结构

```text
DormitoryManagementSys/
├─ database/
│  ├─ schema.sql          # 建库、建表、视图
│  ├─ seed.sql            # 院系/楼栋/房间/资产类别等演示数据
│  ├─ reset.sql           # 开发环境重置（会删除数据）
│  └─ README.md
├─ docs/
│  ├─ database-design.md  # 数据库设计说明书
│  └─ reference/          # 需求草图、ER/DFD 参考图片
├─ .env.example           # 环境变量模板
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

## 说明

- 详细表结构、字段说明、状态机和权限矩阵见 [数据库设计文档](docs/database-design.md)。
- 当前仓库为公开仓库，禁止提交 `.env`、数据库密码、JWT 密钥、真实学生信息和访客证件照。
- 登录账号不预置在种子数据中，后续由后端初始化脚本创建，避免在公开仓库中存放默认密码。
