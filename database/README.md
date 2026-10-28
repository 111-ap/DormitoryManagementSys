# 数据库脚本说明

## 文件

| 文件 | 作用 | 是否破坏数据 |
|---|---|---|
| `schema.sql` | 创建 `dormitory_db`、20 张表、2 个视图 | 否（只建不删） |
| `seed.sql` | 写入院系、楼栋、房间、资产类别、水电账户和少量资产 | 否（`INSERT IGNORE`） |
| `reset.sql` | 删除所有业务表和视图 | **是**，仅用于本地开发 |

## 初始化

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql
```

## 重置

```bash
mysql -u root -p < database/reset.sql
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql
```

## 当前数据库

- 数据库：`dormitory_db`
- 字符集：`utf8mb4`
- 排序规则：`utf8mb4_0900_ai_ci`
- 应用账号：`dorm_app`（只授权 `dormitory_db.*`）
- 应用连接信息：项目根目录 `.env`（已被 `.gitignore` 忽略）

## 设计要点

- 学生住宿历史通过 `room_assignments` 保留，不物理删除；
- 生成列 `active_student_id`、`active_bed_key` 保证一个学生只有一条当前住宿、一个床位只住一人；
- `utility_bills` 的水费、电费、合计金额使用生成列自动计算；
- `utility_transactions` 记录所有余额变动，充值/缴费必须与余额更新在同一事务中；
- 详细设计见 `docs/database-design.md`。

## 注意

- `reset.sql` 是破坏性脚本，不要在生产环境执行。
- `seed.sql` 不包含任何登录账号或密码。
- MySQL 26.10 是 Innovation 版；如遇驱动兼容问题，可切换到 MySQL 8.4 LTS。
