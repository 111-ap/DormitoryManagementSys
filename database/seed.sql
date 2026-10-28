-- ============================================================
-- 基础演示数据
-- 说明：
--   1. 只包含院系、楼栋、房间、资产类别、水电账户和少量资产。
--   2. 不包含任何登录账号和密码；管理员账号由后端初始化脚本创建。
--   3. 使用 INSERT IGNORE，重复执行不会产生重复数据。
-- ============================================================

USE dormitory_db;

SET NAMES utf8mb4;

-- 院系
INSERT IGNORE INTO departments (code, name) VALUES
  ('CS', '计算机科学与技术学院'),
  ('SE', '软件学院'),
  ('EE', '电子信息学院'),
  ('ME', '机械工程学院');

-- 楼栋
INSERT IGNORE INTO buildings (code, name, address, floors, gender) VALUES
  ('B01', '1号楼', '东区', 6, 'male'),
  ('B02', '2号楼', '东区', 6, 'female'),
  ('B03', '3号楼', '西区', 5, 'mixed');

-- 房间
INSERT IGNORE INTO rooms (building_id, room_no, floor, phone, capacity, gender, status)
SELECT id, '101', 1, '010-0000-0101', 4, 'male', 'normal' FROM buildings WHERE code = 'B01';
INSERT IGNORE INTO rooms (building_id, room_no, floor, phone, capacity, gender, status)
SELECT id, '102', 1, '010-0000-0102', 4, 'male', 'normal' FROM buildings WHERE code = 'B01';
INSERT IGNORE INTO rooms (building_id, room_no, floor, phone, capacity, gender, status)
SELECT id, '103', 1, '010-0000-0103', 4, 'male', 'normal' FROM buildings WHERE code = 'B01';
INSERT IGNORE INTO rooms (building_id, room_no, floor, phone, capacity, gender, status)
SELECT id, '104', 1, '010-0000-0104', 4, 'male', 'normal' FROM buildings WHERE code = 'B01';

INSERT IGNORE INTO rooms (building_id, room_no, floor, phone, capacity, gender, status)
SELECT id, '201', 2, '010-0000-0201', 4, 'female', 'normal' FROM buildings WHERE code = 'B02';
INSERT IGNORE INTO rooms (building_id, room_no, floor, phone, capacity, gender, status)
SELECT id, '202', 2, '010-0000-0202', 4, 'female', 'normal' FROM buildings WHERE code = 'B02';
INSERT IGNORE INTO rooms (building_id, room_no, floor, phone, capacity, gender, status)
SELECT id, '203', 2, '010-0000-0203', 4, 'female', 'normal' FROM buildings WHERE code = 'B02';
INSERT IGNORE INTO rooms (building_id, room_no, floor, phone, capacity, gender, status)
SELECT id, '204', 2, '010-0000-0204', 4, 'female', 'normal' FROM buildings WHERE code = 'B02';

INSERT IGNORE INTO rooms (building_id, room_no, floor, phone, capacity, gender, status)
SELECT id, '301', 3, '010-0000-0301', 4, 'mixed', 'normal' FROM buildings WHERE code = 'B03';
INSERT IGNORE INTO rooms (building_id, room_no, floor, phone, capacity, gender, status)
SELECT id, '302', 3, '010-0000-0302', 4, 'mixed', 'normal' FROM buildings WHERE code = 'B03';

-- 资产类别
INSERT IGNORE INTO asset_categories (code, name) VALUES
  ('BED', '床铺'),
  ('CABINET', '柜子'),
  ('DESK', '桌椅'),
  ('LIGHT', '电灯'),
  ('DOOR', '门窗'),
  ('TOILET', '卫生间设施');

-- 每个房间一个水电账户
INSERT IGNORE INTO utility_accounts (room_id)
SELECT id FROM rooms;

-- 少量资产，便于演示报修
INSERT IGNORE INTO assets (asset_no, category_id, room_id, name, brand, status) VALUES
  ('B01-101-BED-01',
   (SELECT id FROM asset_categories WHERE code = 'BED'),
   (SELECT r.id FROM rooms r JOIN buildings b ON b.id = r.building_id WHERE b.code = 'B01' AND r.room_no = '101'),
   '上下铺', '标准', 'normal'),
  ('B01-101-CABINET-01',
   (SELECT id FROM asset_categories WHERE code = 'CABINET'),
   (SELECT r.id FROM rooms r JOIN buildings b ON b.id = r.building_id WHERE b.code = 'B01' AND r.room_no = '101'),
   '四门衣柜', '标准', 'normal'),
  ('B01-101-LIGHT-01',
   (SELECT id FROM asset_categories WHERE code = 'LIGHT'),
   (SELECT r.id FROM rooms r JOIN buildings b ON b.id = r.building_id WHERE b.code = 'B01' AND r.room_no = '101'),
   '吸顶灯', '标准', 'normal'),
  ('B02-201-BED-01',
   (SELECT id FROM asset_categories WHERE code = 'BED'),
   (SELECT r.id FROM rooms r JOIN buildings b ON b.id = r.building_id WHERE b.code = 'B02' AND r.room_no = '201'),
   '上下铺', '标准', 'normal'),
  ('B02-201-CABINET-01',
   (SELECT id FROM asset_categories WHERE code = 'CABINET'),
   (SELECT r.id FROM rooms r JOIN buildings b ON b.id = r.building_id WHERE b.code = 'B02' AND r.room_no = '201'),
   '四门衣柜', '标准', 'normal'),
  ('B02-201-LIGHT-01',
   (SELECT id FROM asset_categories WHERE code = 'LIGHT'),
   (SELECT r.id FROM rooms r JOIN buildings b ON b.id = r.building_id WHERE b.code = 'B02' AND r.room_no = '201'),
   '吸顶灯', '标准', 'normal'),
  ('B03-301-BED-01',
   (SELECT id FROM asset_categories WHERE code = 'BED'),
   (SELECT r.id FROM rooms r JOIN buildings b ON b.id = r.building_id WHERE b.code = 'B03' AND r.room_no = '301'),
   '单人床', '标准', 'normal'),
  ('B03-301-CABINET-01',
   (SELECT id FROM asset_categories WHERE code = 'CABINET'),
   (SELECT r.id FROM rooms r JOIN buildings b ON b.id = r.building_id WHERE b.code = 'B03' AND r.room_no = '301'),
   '双门衣柜', '标准', 'normal'),
  ('B03-301-LIGHT-01',
   (SELECT id FROM asset_categories WHERE code = 'LIGHT'),
   (SELECT r.id FROM rooms r JOIN buildings b ON b.id = r.building_id WHERE b.code = 'B03' AND r.room_no = '301'),
   '吸顶灯', '标准', 'normal');
