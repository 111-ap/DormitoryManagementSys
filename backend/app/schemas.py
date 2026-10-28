from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

Role = Literal["sys_admin", "building_admin", "worker", "student"]
UserStatus = Literal["active", "disabled"]
Gender = Literal["male", "female", "other"]
RoomGender = Literal["male", "female", "mixed"]
BuildingStatus = Literal["active", "disabled"]
RoomStatus = Literal["normal", "maintenance", "closed"]
AssignmentStatus = Literal["active", "transferring", "checked_out"]
AssetStatus = Literal["normal", "repairing", "scrapped", "idle"]
RepairPriority = Literal["low", "normal", "high", "urgent"]
RepairStatus = Literal["pending", "processing", "completed", "cancelled"]
BillStatus = Literal["unpaid", "paid", "cancelled"]
RechargeStatus = Literal["pending", "success", "failed", "cancelled"]
PayMethod = Literal["wechat_mock", "alipay_mock", "admin_cash"]
VisitorStatus = Literal["visiting", "left", "cancelled"]
ItemDirection = Literal["in", "out"]
ItemStatus = Literal["pending", "approved", "rejected"]
NoticeScope = Literal["building", "room"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class Message(BaseModel):
    message: str


# -------------------------
# Auth / users
# -------------------------

class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class UserOut(ORMModel):
    id: int
    username: str
    real_name: str
    role: Role
    phone: str | None = None
    email: str | None = None
    status: UserStatus
    last_login_at: datetime | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    real_name: str = Field(min_length=1, max_length=50)
    role: Role
    phone: str | None = None
    email: str | None = None


class UserUpdate(BaseModel):
    real_name: str | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)
    phone: str | None = None
    email: str | None = None
    status: UserStatus | None = None


class UserBuildingsUpdate(BaseModel):
    building_ids: list[int]


# -------------------------
# Organization
# -------------------------

class DepartmentCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=100)
    status: BuildingStatus = "active"


class DepartmentOut(ORMModel):
    id: int
    code: str
    name: str
    status: str


class BuildingCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=100)
    address: str | None = None
    floors: int = Field(default=6, ge=1, le=100)
    gender: RoomGender = "mixed"
    status: BuildingStatus = "active"


class BuildingOut(ORMModel):
    id: int
    code: str
    name: str
    address: str | None
    floors: int
    gender: RoomGender
    status: BuildingStatus


class RoomCreate(BaseModel):
    building_id: int
    room_no: str = Field(min_length=1, max_length=20)
    floor: int = Field(ge=1, le=100)
    phone: str | None = None
    capacity: int = Field(default=4, ge=1, le=20)
    gender: RoomGender = "mixed"
    status: RoomStatus = "normal"
    remark: str | None = None


class RoomUpdate(BaseModel):
    phone: str | None = None
    capacity: int | None = Field(default=None, ge=1, le=20)
    gender: RoomGender | None = None
    status: RoomStatus | None = None
    remark: str | None = None


class RoomOut(ORMModel):
    id: int
    building_id: int
    building_name: str | None = None
    room_no: str
    floor: int
    phone: str | None
    capacity: int
    gender: RoomGender
    status: RoomStatus
    occupied_count: int | None = None
    available_beds: int | None = None


# -------------------------
# Students / assignments
# -------------------------

class StudentCreate(BaseModel):
    student_no: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=50)
    gender: Gender = "other"
    department_id: int | None = None
    class_name: str | None = None
    phone: str | None = None
    is_dorm_leader: bool = False
    user_id: int | None = None


class StudentUpdate(BaseModel):
    name: str | None = None
    gender: Gender | None = None
    department_id: int | None = None
    class_name: str | None = None
    phone: str | None = None
    is_dorm_leader: bool | None = None
    status: Literal["active", "graduated", "suspended"] | None = None


class StudentOut(ORMModel):
    id: int
    user_id: int | None
    student_no: str
    name: str
    gender: Gender
    department_id: int | None
    department_name: str | None = None
    class_name: str | None
    phone: str | None
    is_dorm_leader: bool
    status: str
    building_id: int | None = None
    building_name: str | None = None
    room_no: str | None = None
    bed_no: str | None = None


class AssignmentCreate(BaseModel):
    student_id: int
    room_id: int
    bed_no: str = Field(min_length=1, max_length=20)
    check_in_at: datetime | None = None
    remark: str | None = None


class TransferRequest(BaseModel):
    new_room_id: int
    new_bed_no: str = Field(min_length=1, max_length=20)
    reason: str | None = None


class AssignmentOut(ORMModel):
    id: int
    student_id: int
    student_no: str | None = None
    student_name: str | None = None
    room_id: int
    building_id: int | None = None
    building_name: str | None = None
    room_no: str | None = None
    bed_no: str
    check_in_at: datetime
    check_out_at: datetime | None
    status: AssignmentStatus
    remark: str | None


# -------------------------
# Assets / repairs
# -------------------------

class AssetCategoryCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=100)
    remark: str | None = None


class AssetCategoryOut(ORMModel):
    id: int
    code: str
    name: str
    remark: str | None


class AssetCreate(BaseModel):
    asset_no: str = Field(min_length=1, max_length=50)
    category_id: int
    room_id: int
    name: str = Field(min_length=1, max_length=100)
    brand: str | None = None
    purchase_date: date | None = None
    status: AssetStatus = "normal"
    remark: str | None = None


class AssetUpdate(BaseModel):
    name: str | None = None
    brand: str | None = None
    purchase_date: date | None = None
    status: AssetStatus | None = None
    remark: str | None = None


class AssetOut(ORMModel):
    id: int
    asset_no: str
    category_id: int
    category_name: str | None = None
    room_id: int
    building_id: int | None = None
    building_name: str | None = None
    room_no: str | None = None
    name: str
    brand: str | None
    purchase_date: date | None
    status: AssetStatus
    remark: str | None


class RepairCreate(BaseModel):
    room_id: int | None = None
    asset_id: int | None = None
    asset_name: str | None = None
    description: str = Field(min_length=1, max_length=2000)
    priority: RepairPriority = "normal"


class RepairAccept(BaseModel):
    pass


class RepairComplete(BaseModel):
    solution: str = Field(min_length=1, max_length=2000)
    resolved_at: datetime | None = None


class RepairCancel(BaseModel):
    reason: str = Field(min_length=1, max_length=255)


class RepairOut(ORMModel):
    id: int
    order_no: str
    room_id: int
    building_id: int | None = None
    building_name: str | None = None
    room_no: str | None = None
    asset_id: int | None
    asset_name: str | None
    reporter_id: int
    reporter_name: str | None = None
    description: str
    priority: RepairPriority
    status: RepairStatus
    handler_id: int | None
    handler_name: str | None = None
    reported_at: datetime
    accepted_at: datetime | None
    resolved_at: datetime | None
    solution: str | None
    cancel_reason: str | None


# -------------------------
# Utilities
# -------------------------

class UtilityAccountOut(ORMModel):
    id: int
    room_id: int
    building_id: int | None = None
    building_name: str | None = None
    room_no: str | None = None
    balance: Decimal
    status: str


class BillCreate(BaseModel):
    room_id: int
    bill_month: date
    water_prev: Decimal = Field(default=Decimal("0"), ge=0)
    water_curr: Decimal = Field(default=Decimal("0"), ge=0)
    water_unit_price: Decimal = Field(default=Decimal("0"), ge=0)
    electricity_prev: Decimal = Field(default=Decimal("0"), ge=0)
    electricity_curr: Decimal = Field(default=Decimal("0"), ge=0)
    electricity_unit_price: Decimal = Field(default=Decimal("0"), ge=0)
    due_date: date | None = None
    remark: str | None = None


class BillOut(ORMModel):
    id: int
    bill_no: str
    room_id: int
    building_id: int | None = None
    building_name: str | None = None
    room_no: str | None = None
    bill_month: date
    water_prev: Decimal
    water_curr: Decimal
    water_unit_price: Decimal
    water_usage: Decimal | None = None
    water_amount: Decimal | None = None
    electricity_prev: Decimal
    electricity_curr: Decimal
    electricity_unit_price: Decimal
    electricity_usage: Decimal | None = None
    electricity_amount: Decimal | None = None
    total_amount: Decimal | None = None
    status: BillStatus
    due_date: date | None
    generated_by: int
    generated_at: datetime
    paid_at: datetime | None
    remark: str | None


class RechargeCreate(BaseModel):
    account_id: int
    amount: Decimal = Field(gt=0, le=Decimal("100000"))
    pay_method: PayMethod = "wechat_mock"
    remark: str | None = None


class RechargeOut(ORMModel):
    id: int
    order_no: str
    account_id: int
    room_id: int | None = None
    room_no: str | None = None
    amount: Decimal
    pay_method: PayMethod
    status: RechargeStatus
    created_by: int
    paid_at: datetime | None
    remark: str | None


class TransactionOut(ORMModel):
    id: int
    account_id: int
    type: str
    amount: Decimal
    balance_after: Decimal
    biz_type: str
    biz_id: int | None
    created_by: int
    created_at: datetime
    remark: str | None


# -------------------------
# Visitors / items / notices
# -------------------------

class VisitorCreate(BaseModel):
    visitor_name: str = Field(min_length=1, max_length=50)
    id_type: str = Field(default="id_card", max_length=20)
    id_no: str | None = Field(default=None, max_length=32)
    phone: str | None = None
    host_student_id: int | None = None
    room_id: int | None = None
    visit_at: datetime | None = None
    reason: str | None = None
    remark: str | None = None


class VisitorOut(ORMModel):
    id: int
    visitor_name: str
    id_type: str
    id_no_masked: str | None = None
    phone: str | None
    host_student_id: int
    host_student_name: str | None = None
    room_id: int
    building_name: str | None = None
    room_no: str | None = None
    visit_at: datetime
    leave_at: datetime | None
    reason: str | None
    status: VisitorStatus
    registered_by: int
    remark: str | None


class ItemCreate(BaseModel):
    item_name: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0, le=10000)
    unit: str | None = None
    direction: ItemDirection
    occurred_at: datetime | None = None
    reason: str | None = None


class ItemReview(BaseModel):
    status: Literal["approved", "rejected"]
    remark: str | None = None


class ItemOut(ORMModel):
    id: int
    room_id: int
    building_name: str | None = None
    room_no: str | None = None
    student_id: int
    student_name: str | None = None
    item_name: str
    quantity: int
    unit: str | None
    direction: ItemDirection
    occurred_at: datetime
    reason: str | None
    status: ItemStatus
    reviewed_by: int | None
    reviewed_at: datetime | None
    review_remark: str | None


class NoticeCreate(BaseModel):
    building_id: int | None = None
    room_id: int | None = None
    title: str = Field(min_length=1, max_length=150)
    content: str = Field(min_length=1, max_length=5000)
    scope: NoticeScope = "building"


class NoticeOut(ORMModel):
    id: int
    building_id: int
    building_name: str | None = None
    room_id: int | None
    room_no: str | None = None
    author_id: int
    author_name: str | None = None
    title: str
    content: str
    scope: NoticeScope
    status: str
    published_at: datetime


class NotificationOut(ORMModel):
    id: int
    type: str
    title: str
    content: str | None
    related_type: str | None
    related_id: int | None
    is_read: bool
    created_at: datetime
    read_at: datetime | None


class AttachmentOut(ORMModel):
    id: int
    biz_type: str
    biz_id: int
    file_name: str
    file_path: str
    file_size: int
    mime_type: str | None
    uploaded_by: int
    created_at: datetime


class DashboardOut(BaseModel):
    data: dict[str, Any]
