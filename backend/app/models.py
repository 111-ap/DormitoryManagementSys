from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)

from app.db.base import Base


class TimestampMixin:
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Department(Base):
    __tablename__ = "departments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(32), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class Building(Base):
    __tablename__ = "buildings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(32), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    address = Column(String(200))
    floors = Column(Integer, nullable=False, default=6)
    gender = Column(String(20), nullable=False, default="mixed")
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    real_name = Column(String(50), nullable=False)
    role = Column(String(20), nullable=False)
    phone = Column(String(30))
    email = Column(String(100))
    status = Column(String(20), nullable=False, default="active")
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class StaffBuilding(Base):
    __tablename__ = "staff_buildings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    building_id = Column(BigInteger, ForeignKey("buildings.id"), nullable=False)
    assigned_at = Column(DateTime, nullable=False, server_default=func.now())


class Room(Base):
    __tablename__ = "rooms"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    building_id = Column(BigInteger, ForeignKey("buildings.id"), nullable=False)
    room_no = Column(String(20), nullable=False)
    floor = Column(Integer, nullable=False)
    phone = Column(String(30))
    capacity = Column(Integer, nullable=False, default=4)
    gender = Column(String(20), nullable=False, default="mixed")
    status = Column(String(20), nullable=False, default="normal")
    remark = Column(String(255))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class Student(Base):
    __tablename__ = "students"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), unique=True)
    student_no = Column(String(32), nullable=False, unique=True)
    name = Column(String(50), nullable=False)
    gender = Column(String(20), nullable=False, default="other")
    department_id = Column(BigInteger, ForeignKey("departments.id"))
    class_name = Column(String(100))
    phone = Column(String(30))
    is_dorm_leader = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class RoomAssignment(Base):
    __tablename__ = "room_assignments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(BigInteger, ForeignKey("students.id"), nullable=False)
    room_id = Column(BigInteger, ForeignKey("rooms.id"), nullable=False)
    bed_no = Column(String(20), nullable=False)
    check_in_at = Column(DateTime, nullable=False, server_default=func.now())
    check_out_at = Column(DateTime)
    status = Column(String(20), nullable=False, default="active")
    remark = Column(String(255))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    active_student_id = Column(
        BigInteger,
        Computed("CASE WHEN check_out_at IS NULL THEN student_id ELSE NULL END", persisted=True),
    )
    active_bed_key = Column(
        String(64),
        Computed(
            "CASE WHEN check_out_at IS NULL THEN CONCAT(room_id, ':', bed_no) ELSE NULL END",
            persisted=True,
        ),
    )


class AssetCategory(Base):
    __tablename__ = "asset_categories"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(32), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    remark = Column(String(255))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class Asset(Base):
    __tablename__ = "assets"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_no = Column(String(50), nullable=False, unique=True)
    category_id = Column(BigInteger, ForeignKey("asset_categories.id"), nullable=False)
    room_id = Column(BigInteger, ForeignKey("rooms.id"), nullable=False)
    name = Column(String(100), nullable=False)
    brand = Column(String(100))
    purchase_date = Column(Date)
    status = Column(String(20), nullable=False, default="normal")
    remark = Column(String(255))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class RepairOrder(Base):
    __tablename__ = "repair_orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_no = Column(String(32), nullable=False, unique=True)
    room_id = Column(BigInteger, ForeignKey("rooms.id"), nullable=False)
    asset_id = Column(BigInteger, ForeignKey("assets.id"))
    asset_name = Column(String(100))
    reporter_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="normal")
    status = Column(String(20), nullable=False, default="pending")
    handler_id = Column(BigInteger, ForeignKey("users.id"))
    reported_at = Column(DateTime, nullable=False, server_default=func.now())
    accepted_at = Column(DateTime)
    resolved_at = Column(DateTime)
    solution = Column(Text)
    cancel_reason = Column(String(255))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class UtilityAccount(Base):
    __tablename__ = "utility_accounts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    room_id = Column(BigInteger, ForeignKey("rooms.id"), nullable=False, unique=True)
    balance = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class UtilityBill(Base):
    __tablename__ = "utility_bills"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bill_no = Column(String(32), nullable=False, unique=True)
    room_id = Column(BigInteger, ForeignKey("rooms.id"), nullable=False)
    bill_month = Column(Date, nullable=False)
    water_prev = Column(Numeric(12, 2), nullable=False, default=0)
    water_curr = Column(Numeric(12, 2), nullable=False, default=0)
    water_unit_price = Column(Numeric(10, 4), nullable=False, default=0)
    electricity_prev = Column(Numeric(12, 2), nullable=False, default=0)
    electricity_curr = Column(Numeric(12, 2), nullable=False, default=0)
    electricity_unit_price = Column(Numeric(10, 4), nullable=False, default=0)
    water_usage = Column(
        Numeric(12, 2), Computed("water_curr - water_prev", persisted=True)
    )
    water_amount = Column(
        Numeric(12, 2),
        Computed("ROUND((water_curr - water_prev) * water_unit_price, 2)", persisted=True),
    )
    electricity_usage = Column(
        Numeric(12, 2), Computed("electricity_curr - electricity_prev", persisted=True)
    )
    electricity_amount = Column(
        Numeric(12, 2),
        Computed(
            "ROUND((electricity_curr - electricity_prev) * electricity_unit_price, 2)",
            persisted=True,
        ),
    )
    total_amount = Column(
        Numeric(12, 2),
        Computed(
            "ROUND((water_curr - water_prev) * water_unit_price, 2) "
            "+ ROUND((electricity_curr - electricity_prev) * electricity_unit_price, 2)",
            persisted=True,
        ),
    )
    status = Column(String(20), nullable=False, default="unpaid")
    due_date = Column(Date)
    generated_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    generated_at = Column(DateTime, nullable=False, server_default=func.now())
    paid_at = Column(DateTime)
    remark = Column(String(255))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class RechargeOrder(Base):
    __tablename__ = "recharge_orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_no = Column(String(32), nullable=False, unique=True)
    account_id = Column(BigInteger, ForeignKey("utility_accounts.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    pay_method = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    paid_at = Column(DateTime)
    remark = Column(String(255))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class UtilityTransaction(Base):
    __tablename__ = "utility_transactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    account_id = Column(BigInteger, ForeignKey("utility_accounts.id"), nullable=False)
    type = Column(String(20), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    balance_after = Column(Numeric(12, 2), nullable=False)
    biz_type = Column(String(20), nullable=False)
    biz_id = Column(BigInteger)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    remark = Column(String(255))


class Visitor(Base):
    __tablename__ = "visitors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    visitor_name = Column(String(50), nullable=False)
    id_type = Column(String(20), nullable=False, default="id_card")
    id_no = Column(String(32))
    phone = Column(String(30))
    host_student_id = Column(BigInteger, ForeignKey("students.id"), nullable=False)
    room_id = Column(BigInteger, ForeignKey("rooms.id"), nullable=False)
    visit_at = Column(DateTime, nullable=False, server_default=func.now())
    leave_at = Column(DateTime)
    reason = Column(String(255))
    status = Column(String(20), nullable=False, default="visiting")
    registered_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    remark = Column(String(255))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class ItemRecord(Base):
    __tablename__ = "item_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    room_id = Column(BigInteger, ForeignKey("rooms.id"), nullable=False)
    student_id = Column(BigInteger, ForeignKey("students.id"), nullable=False)
    item_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit = Column(String(20))
    direction = Column(String(10), nullable=False)
    occurred_at = Column(DateTime, nullable=False, server_default=func.now())
    reason = Column(String(255))
    status = Column(String(20), nullable=False, default="pending")
    reviewed_by = Column(BigInteger, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    review_remark = Column(String(255))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class Notice(Base):
    __tablename__ = "notices"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    building_id = Column(BigInteger, ForeignKey("buildings.id"), nullable=False)
    room_id = Column(BigInteger, ForeignKey("rooms.id"))
    author_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    content = Column(Text, nullable=False)
    scope = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="published")
    published_at = Column(DateTime, nullable=False, server_default=func.now())
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(150), nullable=False)
    content = Column(String(500))
    related_type = Column(String(50))
    related_id = Column(BigInteger)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    read_at = Column(DateTime)


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    biz_type = Column(String(20), nullable=False)
    biz_id = Column(BigInteger, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False, default=0)
    mime_type = Column(String(100))
    uploaded_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(BigInteger)
    detail = Column(JSON)
    ip = Column(String(45))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
