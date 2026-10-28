# 后端服务

FastAPI + SQLAlchemy + MySQL，API 前缀 `/api/v1`。

## 1. 环境

- Python 3.11
- MySQL 8.0+ / 当前 MySQL 26.10
- 虚拟环境：`backend/.venv`

## 2. 安装依赖

```bash
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

## 3. 初始化数据库

在项目根目录执行：

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql
```

数据库连接信息在根目录 `.env`，该文件已被 `.gitignore` 忽略。

## 4. 创建管理员

```bash
cd backend
.venv\Scripts\python.exe scripts\create_admin.py
```

管理员账号和初始密码来自 `.env` 的 `ADMIN_USERNAME`、`ADMIN_INITIAL_PASSWORD`。

## 5. 启动

```bash
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/api/v1/health>
- OpenAPI：<http://127.0.0.1:8000/api/v1/openapi.json>

## 6. 冒烟测试

```bash
cd backend
.venv\Scripts\python.exe scripts\smoke_test.py
```

会写入测试数据，测试后可用 `database/reset.sql` 重置。

## 7. 目录

```text
app/
├─ main.py
├─ core/          # 配置、安全、依赖
├─ db/            # SQLAlchemy 会话
├─ models.py      # ORM 模型
├─ schemas.py     # Pydantic 模型
├─ services/      # 通用服务、通知、序列化
└─ api/v1/        # 路由
scripts/
├─ create_admin.py
└─ smoke_test.py
```

详细设计见 `docs/backend-design.md`。
