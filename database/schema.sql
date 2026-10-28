-- ============================================================
-- 高校学生宿舍信息管理系统 - 数据库结构
-- 目标数据库：MySQL 8.0.16+ / MySQL 26.10
-- 字符集：utf8mb4 / utf8mb4_0900_ai_ci
--
-- 说明：
--   1. 本脚本只创建表，不主动删除已有表。
--   2. 需要重置开发库时，使用 database/reset.sql。
--   3. 所有表名、字段名使用小写 snake_case。
-- ============================================================

CREATE DATABASE IF NOT EXISTS dormitory_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE dormitory_db;

SET NAMES utf8mb4;

-- ------------------------------------------------------------
-- 1. 组织与账号
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS departments (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '院系ID',
  code        VARCHAR(32)     NOT NULL COMMENT '院系编码',
  name        VARCHAR(100)    NOT NULL COMMENT '院系名称',
  status      ENUM('active','disabled') NOT NULL DEFAULT 'active' COMMENT '状态',
  created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_departments_code (code),
  KEY idx_departments_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='院系';

CREATE TABLE IF NOT EXISTS buildings (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '楼栋ID',
  code        VARCHAR(32)     NOT NULL COMMENT '楼栋编码',
  name        VARCHAR(100)    NOT NULL COMMENT '楼栋名称',
  address     VARCHAR(200)    NULL COMMENT '地址',
  floors      TINYINT UNSIGNED NOT NULL DEFAULT 6 COMMENT '楼层数',
  gender      ENUM('male','female','mixed') NOT NULL DEFAULT 'mixed' COMMENT '楼栋性别限制',
  status      ENUM('active','disabled') NOT NULL DEFAULT 'active' COMMENT '状态',
  created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_buildings_code (code),
  KEY idx_buildings_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='宿舍楼';

CREATE TABLE IF NOT EXISTS users (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  username       VARCHAR(50)     NOT NULL COMMENT '登录名',
  password_hash  VARCHAR(255)    NOT NULL COMMENT '密码哈希（bcrypt）',
  real_name      VARCHAR(50)     NOT NULL COMMENT '姓名',
  role           ENUM('sys_admin','building_admin','worker','student') NOT NULL COMMENT '角色',
  phone          VARCHAR(30)     NULL COMMENT '联系电话',
  email          VARCHAR(100)    NULL COMMENT '邮箱',
  status         ENUM('active','disabled') NOT NULL DEFAULT 'active' COMMENT '账号状态',
  last_login_at  DATETIME        NULL COMMENT '最后登录时间',
  created_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_username (username),
  KEY idx_users_role (role),
  KEY idx_users_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统用户';

CREATE TABLE IF NOT EXISTS staff_buildings (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'ID',
  user_id      BIGINT UNSIGNED NOT NULL COMMENT '员工用户ID',
  building_id  BIGINT UNSIGNED NOT NULL COMMENT '楼栋ID',
  assigned_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '分配时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_staff_buildings_user_building (user_id, building_id),
  KEY idx_staff_buildings_building (building_id),
  CONSTRAINT fk_staff_buildings_user
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_staff_buildings_building
    FOREIGN KEY (building_id) REFERENCES buildings (id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='员工负责楼栋';

-- ------------------------------------------------------------
-- 2. 房间、学生与住宿历史
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS rooms (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '房间ID',
  building_id  BIGINT UNSIGNED NOT NULL COMMENT '楼栋ID',
  room_no      VARCHAR(20)     NOT NULL COMMENT '房间号',
  floor        TINYINT UNSIGNED NOT NULL COMMENT '楼层',
  phone        VARCHAR(30)     NULL COMMENT '房间电话',
  capacity     TINYINT UNSIGNED NOT NULL DEFAULT 4 COMMENT '可住人数',
  gender       ENUM('male','female','mixed') NOT NULL DEFAULT 'mixed' COMMENT '房间性别限制',
  status       ENUM('normal','maintenance','closed') NOT NULL DEFAULT 'normal' COMMENT '房间状态',
  remark       VARCHAR(255)    NULL COMMENT '备注',
  created_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_rooms_building_room_no (building_id, room_no),
  KEY idx_rooms_building_status (building_id, status),
  KEY idx_rooms_phone (phone),
  CONSTRAINT fk_rooms_building
    FOREIGN KEY (building_id) REFERENCES buildings (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT chk_rooms_capacity CHECK (capacity > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='宿舍房间';

CREATE TABLE IF NOT EXISTS students (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '学生ID',
  user_id         BIGINT UNSIGNED NULL COMMENT '关联登录账号',
  student_no      VARCHAR(32)     NOT NULL COMMENT '学号',
  name            VARCHAR(50)     NOT NULL COMMENT '姓名',
  gender          ENUM('male','female','other') NOT NULL DEFAULT 'other' COMMENT '性别',
  department_id   BIGINT UNSIGNED NULL COMMENT '院系ID',
  class_name      VARCHAR(100)    NULL COMMENT '班级',
  phone           VARCHAR(30)     NULL COMMENT '联系电话',
  is_dorm_leader  TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '是否舍长：1是，0否',
  status          ENUM('active','graduated','suspended') NOT NULL DEFAULT 'active' COMMENT '学籍状态',
  created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_students_student_no (student_no),
  UNIQUE KEY uk_students_user_id (user_id),
  KEY idx_students_department (department_id),
  KEY idx_students_status (status),
  CONSTRAINT fk_students_user
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_students_department
    FOREIGN KEY (department_id) REFERENCES departments (id) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT chk_students_dorm_leader CHECK (is_dorm_leader IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='学生档案';

CREATE TABLE IF NOT EXISTS room_assignments (
  id                 BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '住宿记录ID',
  student_id         BIGINT UNSIGNED NOT NULL COMMENT '学生ID',
  room_id            BIGINT UNSIGNED NOT NULL COMMENT '房间ID',
  bed_no             VARCHAR(20)     NOT NULL COMMENT '床位号',
  check_in_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入住时间',
  check_out_at       DATETIME        NULL COMMENT '退宿时间；空表示当前在住',
  status             ENUM('active','transferring','checked_out') NOT NULL DEFAULT 'active' COMMENT '住宿状态',
  remark             VARCHAR(255)    NULL COMMENT '备注',
  created_at         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  active_student_id  BIGINT UNSIGNED GENERATED ALWAYS AS (
    CASE WHEN check_out_at IS NULL THEN student_id ELSE NULL END
  ) STORED COMMENT '在住学生唯一键，用于约束一人只能有一条当前住宿记录',
  active_bed_key     VARCHAR(64)     GENERATED ALWAYS AS (
    CASE WHEN check_out_at IS NULL THEN CONCAT(room_id, ':', bed_no) ELSE NULL END
  ) STORED COMMENT '在住床位唯一键，用于约束一个床位只能住一人',
  PRIMARY KEY (id),
  UNIQUE KEY uk_assign_active_student (active_student_id),
  UNIQUE KEY uk_assign_active_bed (active_bed_key),
  KEY idx_assign_student_history (student_id, check_in_at),
  KEY idx_assign_room_current (room_id, check_out_at),
  KEY idx_assign_status (status),
  -- 注意：student_id / room_id 被生成列引用，不能使用 ON UPDATE CASCADE
  CONSTRAINT fk_assign_student
    FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_assign_room
    FOREIGN KEY (room_id) REFERENCES rooms (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT chk_assign_dates CHECK (check_out_at IS NULL OR check_out_at >= check_in_at),
  CONSTRAINT chk_assign_status_dates CHECK (
    (status = 'checked_out' AND check_out_at IS NOT NULL)
    OR (status <> 'checked_out' AND check_out_at IS NULL)
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='住宿记录（保留历史）';

-- ------------------------------------------------------------
-- 3. 资产与报修
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS asset_categories (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '资产类别ID',
  code        VARCHAR(32)     NOT NULL COMMENT '类别编码',
  name        VARCHAR(100)    NOT NULL COMMENT '类别名称',
  remark      VARCHAR(255)    NULL COMMENT '备注',
  created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_asset_categories_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='资产类别';

CREATE TABLE IF NOT EXISTS assets (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '资产ID',
  asset_no       VARCHAR(50)     NOT NULL COMMENT '资产编号',
  category_id    BIGINT UNSIGNED NOT NULL COMMENT '资产类别ID',
  room_id        BIGINT UNSIGNED NOT NULL COMMENT '所属房间ID',
  name           VARCHAR(100)    NOT NULL COMMENT '资产名称',
  brand          VARCHAR(100)    NULL COMMENT '品牌/规格',
  purchase_date  DATE            NULL COMMENT '购置日期',
  status         ENUM('normal','repairing','scrapped','idle') NOT NULL DEFAULT 'normal' COMMENT '资产状态',
  remark         VARCHAR(255)    NULL COMMENT '备注',
  created_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_assets_asset_no (asset_no),
  KEY idx_assets_room (room_id),
  KEY idx_assets_category (category_id),
  KEY idx_assets_status (status),
  CONSTRAINT fk_assets_category
    FOREIGN KEY (category_id) REFERENCES asset_categories (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_assets_room
    FOREIGN KEY (room_id) REFERENCES rooms (id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='宿舍资产';

CREATE TABLE IF NOT EXISTS repair_orders (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '报修单ID',
  order_no       VARCHAR(32)     NOT NULL COMMENT '报修单号',
  room_id        BIGINT UNSIGNED NOT NULL COMMENT '报修房间ID',
  asset_id       BIGINT UNSIGNED NULL COMMENT '报修资产ID；未入账资产可为空',
  asset_name     VARCHAR(100)    NULL COMMENT '未入账资产名称',
  reporter_id    BIGINT UNSIGNED NOT NULL COMMENT '报修人用户ID',
  description    TEXT            NOT NULL COMMENT '损坏原因/故障描述',
  priority       ENUM('low','normal','high','urgent') NOT NULL DEFAULT 'normal' COMMENT '优先级',
  status         ENUM('pending','processing','completed','cancelled') NOT NULL DEFAULT 'pending' COMMENT '状态',
  handler_id     BIGINT UNSIGNED NULL COMMENT '处理人（水电工）用户ID',
  reported_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '报修时间',
  accepted_at    DATETIME        NULL COMMENT '接单时间',
  resolved_at    DATETIME        NULL COMMENT '解决时间',
  solution       TEXT            NULL COMMENT '处理方案',
  cancel_reason  VARCHAR(255)    NULL COMMENT '取消原因',
  created_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_repair_orders_order_no (order_no),
  KEY idx_repair_room (room_id),
  KEY idx_repair_asset (asset_id),
  KEY idx_repair_reporter (reporter_id),
  KEY idx_repair_handler (handler_id),
  KEY idx_repair_status_time (status, reported_at),
  CONSTRAINT fk_repair_room
    FOREIGN KEY (room_id) REFERENCES rooms (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_repair_asset
    FOREIGN KEY (asset_id) REFERENCES assets (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_repair_reporter
    FOREIGN KEY (reporter_id) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_repair_handler
    FOREIGN KEY (handler_id) REFERENCES users (id) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT chk_repair_resolved CHECK (resolved_at IS NULL OR resolved_at >= reported_at),
  CONSTRAINT chk_repair_completed CHECK (status <> 'completed' OR resolved_at IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='报修单';

-- ------------------------------------------------------------
-- 4. 水电账户、账单、充值与流水
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS utility_accounts (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '水电账户ID',
  room_id     BIGINT UNSIGNED NOT NULL COMMENT '房间ID',
  balance     DECIMAL(12,2)   NOT NULL DEFAULT 0.00 COMMENT '当前余额',
  status      ENUM('active','frozen') NOT NULL DEFAULT 'active' COMMENT '账户状态',
  created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_utility_accounts_room (room_id),
  CONSTRAINT fk_utility_accounts_room
    FOREIGN KEY (room_id) REFERENCES rooms (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT chk_utility_accounts_balance CHECK (balance >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='房间水电账户';

CREATE TABLE IF NOT EXISTS utility_bills (
  id                    BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '账单ID',
  bill_no               VARCHAR(32)     NOT NULL COMMENT '账单号',
  room_id               BIGINT UNSIGNED NOT NULL COMMENT '房间ID',
  bill_month            DATE            NOT NULL COMMENT '账单月份，固定为当月1日',
  water_prev            DECIMAL(12,2)   NOT NULL DEFAULT 0.00 COMMENT '水表上期读数',
  water_curr            DECIMAL(12,2)   NOT NULL DEFAULT 0.00 COMMENT '水表本期读数',
  water_unit_price      DECIMAL(10,4)   NOT NULL DEFAULT 0.0000 COMMENT '水价快照',
  electricity_prev      DECIMAL(12,2)   NOT NULL DEFAULT 0.00 COMMENT '电表上期读数',
  electricity_curr      DECIMAL(12,2)   NOT NULL DEFAULT 0.00 COMMENT '电表本期读数',
  electricity_unit_price DECIMAL(10,4)  NOT NULL DEFAULT 0.0000 COMMENT '电价快照',
  water_usage           DECIMAL(12,2)   GENERATED ALWAYS AS (water_curr - water_prev) STORED COMMENT '用水量',
  water_amount          DECIMAL(12,2)   GENERATED ALWAYS AS (ROUND((water_curr - water_prev) * water_unit_price, 2)) STORED COMMENT '水费',
  electricity_usage     DECIMAL(12,2)   GENERATED ALWAYS AS (electricity_curr - electricity_prev) STORED COMMENT '用电量',
  electricity_amount    DECIMAL(12,2)   GENERATED ALWAYS AS (ROUND((electricity_curr - electricity_prev) * electricity_unit_price, 2)) STORED COMMENT '电费',
  total_amount          DECIMAL(12,2)   GENERATED ALWAYS AS (
    ROUND((water_curr - water_prev) * water_unit_price, 2)
    + ROUND((electricity_curr - electricity_prev) * electricity_unit_price, 2)
  ) STORED COMMENT '账单合计',
  status                ENUM('unpaid','paid','cancelled') NOT NULL DEFAULT 'unpaid' COMMENT '账单状态',
  due_date              DATE            NULL COMMENT '缴费截止日',
  generated_by          BIGINT UNSIGNED NOT NULL COMMENT '生成人用户ID',
  generated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
  paid_at               DATETIME        NULL COMMENT '缴费时间',
  remark                VARCHAR(255)    NULL COMMENT '备注',
  created_at            DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at            DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_utility_bills_no (bill_no),
  UNIQUE KEY uk_utility_bills_room_month (room_id, bill_month),
  KEY idx_utility_bills_status (status),
  KEY idx_utility_bills_month (bill_month),
  CONSTRAINT fk_utility_bills_room
    FOREIGN KEY (room_id) REFERENCES rooms (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_utility_bills_generator
    FOREIGN KEY (generated_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT chk_utility_bills_month CHECK (DAYOFMONTH(bill_month) = 1),
  CONSTRAINT chk_utility_bills_water CHECK (water_curr >= water_prev),
  CONSTRAINT chk_utility_bills_electricity CHECK (electricity_curr >= electricity_prev)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='月度水电合并账单';

CREATE TABLE IF NOT EXISTS recharge_orders (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '充值订单ID',
  order_no    VARCHAR(32)     NOT NULL COMMENT '订单号',
  account_id  BIGINT UNSIGNED NOT NULL COMMENT '水电账户ID',
  amount      DECIMAL(12,2)   NOT NULL COMMENT '充值金额',
  pay_method  ENUM('wechat_mock','alipay_mock','admin_cash') NOT NULL COMMENT '支付方式（模拟）',
  status      ENUM('pending','success','failed','cancelled') NOT NULL DEFAULT 'pending' COMMENT '订单状态',
  created_by  BIGINT UNSIGNED NOT NULL COMMENT '发起人用户ID',
  paid_at     DATETIME        NULL COMMENT '支付成功时间',
  remark      VARCHAR(255)    NULL COMMENT '备注',
  created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_recharge_orders_no (order_no),
  KEY idx_recharge_account (account_id),
  KEY idx_recharge_status (status),
  KEY idx_recharge_created_by (created_by),
  CONSTRAINT fk_recharge_account
    FOREIGN KEY (account_id) REFERENCES utility_accounts (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_recharge_creator
    FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT chk_recharge_amount CHECK (amount > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='模拟充值订单';

CREATE TABLE IF NOT EXISTS utility_transactions (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '流水ID',
  account_id     BIGINT UNSIGNED NOT NULL COMMENT '水电账户ID',
  type           ENUM('recharge','bill_payment','adjustment','refund') NOT NULL COMMENT '流水类型',
  amount         DECIMAL(12,2)   NOT NULL COMMENT '变动金额：充值正数，缴费负数',
  balance_after  DECIMAL(12,2)   NOT NULL COMMENT '变动后余额',
  biz_type       ENUM('recharge_order','utility_bill','manual') NOT NULL COMMENT '业务类型',
  biz_id         BIGINT UNSIGNED NULL COMMENT '业务ID',
  created_by     BIGINT UNSIGNED NOT NULL COMMENT '操作人用户ID',
  created_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  remark         VARCHAR(255)    NULL COMMENT '备注',
  PRIMARY KEY (id),
  KEY idx_utility_tx_account_time (account_id, created_at),
  KEY idx_utility_tx_biz (biz_type, biz_id),
  CONSTRAINT fk_utility_tx_account
    FOREIGN KEY (account_id) REFERENCES utility_accounts (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_utility_tx_creator
    FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT chk_utility_tx_amount CHECK (amount <> 0),
  CONSTRAINT chk_utility_tx_balance CHECK (balance_after >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='水电账户余额流水';

-- ------------------------------------------------------------
-- 5. 访客、物品出入、公告与通知
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS visitors (
  id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '访客记录ID',
  visitor_name     VARCHAR(50)     NOT NULL COMMENT '访客姓名',
  id_type          VARCHAR(20)     NOT NULL DEFAULT 'id_card' COMMENT '证件类型',
  id_no            VARCHAR(32)     NULL COMMENT '证件号码（敏感，界面脱敏）',
  phone            VARCHAR(30)     NULL COMMENT '访客电话',
  host_student_id  BIGINT UNSIGNED NOT NULL COMMENT '被访学生ID',
  room_id          BIGINT UNSIGNED NOT NULL COMMENT '被访房间ID',
  visit_at         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '来访时间',
  leave_at         DATETIME        NULL COMMENT '离开时间',
  reason           VARCHAR(255)    NULL COMMENT '来访事由',
  status           ENUM('visiting','left','cancelled') NOT NULL DEFAULT 'visiting' COMMENT '状态',
  registered_by    BIGINT UNSIGNED NOT NULL COMMENT '登记人用户ID',
  remark           VARCHAR(255)    NULL COMMENT '备注',
  created_at       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_visitors_room_time (room_id, visit_at),
  KEY idx_visitors_host (host_student_id),
  KEY idx_visitors_status (status),
  CONSTRAINT fk_visitors_host
    FOREIGN KEY (host_student_id) REFERENCES students (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_visitors_room
    FOREIGN KEY (room_id) REFERENCES rooms (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_visitors_registrar
    FOREIGN KEY (registered_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT chk_visitors_leave CHECK (leave_at IS NULL OR leave_at >= visit_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='访客登记';

CREATE TABLE IF NOT EXISTS item_records (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '物品出入记录ID',
  room_id        BIGINT UNSIGNED NOT NULL COMMENT '房间ID',
  student_id     BIGINT UNSIGNED NOT NULL COMMENT '登记学生ID',
  item_name      VARCHAR(100)    NOT NULL COMMENT '物品名称',
  quantity       INT UNSIGNED    NOT NULL COMMENT '数量',
  unit           VARCHAR(20)     NULL COMMENT '单位',
  direction      ENUM('in','out') NOT NULL COMMENT '出入方向',
  occurred_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发生时间',
  reason         VARCHAR(255)    NULL COMMENT '事由',
  status         ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending' COMMENT '审核状态',
  reviewed_by    BIGINT UNSIGNED NULL COMMENT '审核人用户ID',
  reviewed_at    DATETIME        NULL COMMENT '审核时间',
  review_remark  VARCHAR(255)    NULL COMMENT '审核意见',
  created_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_item_room_time (room_id, occurred_at),
  KEY idx_item_student (student_id),
  KEY idx_item_status (status),
  CONSTRAINT fk_item_room
    FOREIGN KEY (room_id) REFERENCES rooms (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_item_student
    FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_item_reviewer
    FOREIGN KEY (reviewed_by) REFERENCES users (id) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT chk_item_quantity CHECK (quantity > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='物品出入登记';

CREATE TABLE IF NOT EXISTS notices (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '公告ID',
  building_id   BIGINT UNSIGNED NOT NULL COMMENT '所属楼栋ID',
  room_id       BIGINT UNSIGNED NULL COMMENT '寝室公告的房间ID；楼栋公告为空',
  author_id     BIGINT UNSIGNED NOT NULL COMMENT '发布人用户ID',
  title         VARCHAR(150)    NOT NULL COMMENT '标题',
  content       TEXT            NOT NULL COMMENT '内容',
  scope         ENUM('building','room') NOT NULL COMMENT '公告范围',
  status        ENUM('published','archived') NOT NULL DEFAULT 'published' COMMENT '状态',
  published_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间',
  created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_notices_building_time (building_id, published_at),
  KEY idx_notices_room_time (room_id, published_at),
  KEY idx_notices_author (author_id),
  CONSTRAINT fk_notices_building
    FOREIGN KEY (building_id) REFERENCES buildings (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_notices_room
    FOREIGN KEY (room_id) REFERENCES rooms (id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_notices_author
    FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='楼栋/寝室公告';

CREATE TABLE IF NOT EXISTS notifications (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '通知ID',
  user_id       BIGINT UNSIGNED NOT NULL COMMENT '接收人用户ID',
  type          VARCHAR(50)     NOT NULL COMMENT '通知类型',
  title         VARCHAR(150)    NOT NULL COMMENT '标题',
  content       VARCHAR(500)    NULL COMMENT '内容',
  related_type  VARCHAR(50)     NULL COMMENT '关联业务类型',
  related_id    BIGINT UNSIGNED NULL COMMENT '关联业务ID',
  is_read       TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '是否已读',
  created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  read_at       DATETIME        NULL COMMENT '阅读时间',
  PRIMARY KEY (id),
  KEY idx_notifications_user_read (user_id, is_read, created_at),
  KEY idx_notifications_related (related_type, related_id),
  CONSTRAINT fk_notifications_user
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT chk_notifications_read CHECK (is_read IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='站内通知';

CREATE TABLE IF NOT EXISTS attachments (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '附件ID',
  biz_type     ENUM('repair','visitor','item','notice') NOT NULL COMMENT '业务类型',
  biz_id       BIGINT UNSIGNED NOT NULL COMMENT '业务ID',
  file_name    VARCHAR(255)    NOT NULL COMMENT '原始文件名',
  file_path    VARCHAR(500)    NOT NULL COMMENT '相对存储路径',
  file_size    BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '文件大小（字节）',
  mime_type    VARCHAR(100)    NULL COMMENT 'MIME类型',
  uploaded_by  BIGINT UNSIGNED NOT NULL COMMENT '上传人用户ID',
  created_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_attachments_biz (biz_type, biz_id),
  KEY idx_attachments_uploader (uploaded_by),
  CONSTRAINT fk_attachments_uploader
    FOREIGN KEY (uploaded_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='业务附件（报修照片、访客证件照等）';

CREATE TABLE IF NOT EXISTS audit_logs (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  user_id      BIGINT UNSIGNED NULL COMMENT '操作人用户ID',
  action       VARCHAR(100)    NOT NULL COMMENT '操作动作',
  entity_type  VARCHAR(50)     NULL COMMENT '业务实体',
  entity_id    BIGINT UNSIGNED NULL COMMENT '业务实体ID',
  detail       JSON            NULL COMMENT '变更详情',
  ip           VARCHAR(45)     NULL COMMENT '客户端IP',
  created_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_audit_user_time (user_id, created_at),
  KEY idx_audit_entity (entity_type, entity_id),
  CONSTRAINT fk_audit_user
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='关键操作审计日志';

-- ------------------------------------------------------------
-- 6. 查询视图
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW v_room_occupancy AS
SELECT
  r.id AS room_id,
  r.building_id,
  b.name AS building_name,
  r.room_no,
  r.floor,
  r.phone,
  r.capacity,
  r.gender,
  r.status,
  (SELECT COUNT(*) FROM room_assignments ra
    WHERE ra.room_id = r.id AND ra.check_out_at IS NULL) AS occupied_count,
  r.capacity - (SELECT COUNT(*) FROM room_assignments ra
    WHERE ra.room_id = r.id AND ra.check_out_at IS NULL) AS available_beds
FROM rooms r
JOIN buildings b ON b.id = r.building_id;

CREATE OR REPLACE VIEW v_student_current_room AS
SELECT
  s.id AS student_id,
  s.student_no,
  s.name AS student_name,
  s.gender AS student_gender,
  d.name AS department_name,
  s.class_name,
  ra.id AS assignment_id,
  ra.room_id,
  b.id AS building_id,
  b.name AS building_name,
  r.room_no,
  ra.bed_no,
  ra.check_in_at
FROM students s
JOIN room_assignments ra ON ra.student_id = s.id AND ra.check_out_at IS NULL
JOIN rooms r ON r.id = ra.room_id
JOIN buildings b ON b.id = r.building_id
LEFT JOIN departments d ON d.id = s.department_id;
