-- ============================================================
-- 开发环境数据库重置脚本
-- 警告：会删除 dormitory_db 中所有表和数据，仅用于本地开发
-- ============================================================

USE dormitory_db;

SET FOREIGN_KEY_CHECKS = 0;

DROP VIEW IF EXISTS v_student_current_room;
DROP VIEW IF EXISTS v_room_occupancy;

DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS attachments;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS notices;
DROP TABLE IF EXISTS item_records;
DROP TABLE IF EXISTS visitors;
DROP TABLE IF EXISTS utility_transactions;
DROP TABLE IF EXISTS recharge_orders;
DROP TABLE IF EXISTS utility_bills;
DROP TABLE IF EXISTS utility_accounts;
DROP TABLE IF EXISTS repair_orders;
DROP TABLE IF EXISTS assets;
DROP TABLE IF EXISTS asset_categories;
DROP TABLE IF EXISTS room_assignments;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS staff_buildings;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS buildings;
DROP TABLE IF EXISTS departments;

SET FOREIGN_KEY_CHECKS = 1;

-- 注意：本脚本不会删除数据库本身，也不删除数据库账号。
-- 重新建表请继续执行 database/schema.sql。
