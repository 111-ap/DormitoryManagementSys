from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import (
    building_ids_for_user,
    current_room_id_for_student,
    ensure_room_access,
    get_current_user,
    require_roles,
)
from app.db.session import get_db
from app.models import (
    Room,
    RoomAssignment,
    Student,
    User,
    UtilityAccount,
    UtilityBill,
    UtilityTransaction,
    RechargeOrder,
)
from app.schemas import (
    BillCreate,
    BillOut,
    Message,
    Page,
    RechargeCreate,
    RechargeOut,
    TransactionOut,
    UtilityAccountOut,
)
from app.services.common import commit_or_400, make_no, paginate
from app.services.notifications import notify
from app.services.serializers import account_dict, bill_dict, recharge_dict

router = APIRouter(prefix="/utilities", tags=["水电费"])
staff_only = require_roles("sys_admin", "building_admin", "worker")


def _ensure_account_access(db: Session, user: User, account: UtilityAccount) -> Room:
    room = db.get(Room, account.room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="房间不存在")
    if user.role == "student":
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        if student is None:
            raise HTTPException(status_code=403, detail="学生档案不存在")
        current_room = current_room_id_for_student(db, student.id)
        if current_room != account.room_id:
            raise HTTPException(status_code=403, detail="只能查看自己房间的水电账户")
    else:
        ensure_room_access(db, user, room.id)
    return room


def _room_user_ids(db: Session, room_id: int) -> list[int]:
    rows = db.scalars(
        select(Student.user_id)
        .join(RoomAssignment, RoomAssignment.student_id == Student.id)
        .where(
            RoomAssignment.room_id == room_id,
            RoomAssignment.check_out_at.is_(None),
            Student.user_id.is_not(None),
        )
    ).all()
    return [x for x in rows if x]


@router.get("/accounts", response_model=Page[UtilityAccountOut], summary="水电账户列表")
def list_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    building_id: int | None = None,
    room_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[UtilityAccountOut]:
    stmt = select(UtilityAccount).order_by(UtilityAccount.id.desc())
    if user.role == "student":
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        if student is None:
            return Page(items=[], total=0, page=page, page_size=page_size)
        current_room = current_room_id_for_student(db, student.id)
        if current_room is None:
            return Page(items=[], total=0, page=page, page_size=page_size)
        stmt = stmt.where(UtilityAccount.room_id == current_room)
    else:
        allowed = building_ids_for_user(db, user)
        if allowed is not None:
            if not allowed:
                return Page(items=[], total=0, page=page, page_size=page_size)
            room_ids = select(Room.id).where(Room.building_id.in_(allowed))
            stmt = stmt.where(UtilityAccount.room_id.in_(room_ids))
    if building_id is not None:
        room_ids = select(Room.id).where(Room.building_id == building_id)
        stmt = stmt.where(UtilityAccount.room_id.in_(room_ids))
    if room_id is not None:
        stmt = stmt.where(UtilityAccount.room_id == room_id)

    rows, total = paginate(db, stmt, page, page_size)
    return Page(
        items=[UtilityAccountOut.model_validate(account_dict(db, x)) for x in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/accounts/room/{room_id}", response_model=UtilityAccountOut, summary="确保房间水电账户")
def ensure_account(
    room_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> UtilityAccountOut:
    ensure_room_access(db, user, room_id)
    account = db.scalar(select(UtilityAccount).where(UtilityAccount.room_id == room_id))
    if account is None:
        account = UtilityAccount(room_id=room_id)
        db.add(account)
        commit_or_400(db)
        db.refresh(account)
    return UtilityAccountOut.model_validate(account_dict(db, account))


@router.get("/accounts/{account_id}/transactions", response_model=Page[TransactionOut], summary="账户流水")
def list_transactions(
    account_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[TransactionOut]:
    account = db.get(UtilityAccount, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="水电账户不存在")
    _ensure_account_access(db, user, account)
    stmt = select(UtilityTransaction).where(UtilityTransaction.account_id == account_id).order_by(UtilityTransaction.id.desc())
    rows, total = paginate(db, stmt, page, page_size)
    return Page(items=[TransactionOut.model_validate(x) for x in rows], total=total, page=page, page_size=page_size)


@router.get("/bills", response_model=Page[BillOut], summary="水电账单列表")
def list_bills(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    room_id: int | None = None,
    bill_month: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[BillOut]:
    stmt = select(UtilityBill).order_by(UtilityBill.bill_month.desc(), UtilityBill.id.desc())
    if user.role == "student":
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        current_room = current_room_id_for_student(db, student.id) if student else None
        if current_room is None:
            return Page(items=[], total=0, page=page, page_size=page_size)
        stmt = stmt.where(UtilityBill.room_id == current_room)
    else:
        allowed = building_ids_for_user(db, user)
        if allowed is not None:
            if not allowed:
                return Page(items=[], total=0, page=page, page_size=page_size)
            room_ids = select(Room.id).where(Room.building_id.in_(allowed))
            stmt = stmt.where(UtilityBill.room_id.in_(room_ids))
    if status:
        stmt = stmt.where(UtilityBill.status == status)
    if room_id is not None:
        stmt = stmt.where(UtilityBill.room_id == room_id)
    if bill_month is not None:
        stmt = stmt.where(UtilityBill.bill_month == bill_month)

    rows, total = paginate(db, stmt, page, page_size)
    return Page(
        items=[BillOut.model_validate(bill_dict(db, x)) for x in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/bills", response_model=BillOut, summary="生成月度水电账单")
def create_bill(
    payload: BillCreate,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> BillOut:
    room = ensure_room_access(db, user, payload.room_id)
    if payload.bill_month.day != 1:
        raise HTTPException(status_code=400, detail="账单月份必须是当月1日")
    if payload.water_curr < payload.water_prev:
        raise HTTPException(status_code=400, detail="水表本期读数不能小于上期")
    if payload.electricity_curr < payload.electricity_prev:
        raise HTTPException(status_code=400, detail="电表本期读数不能小于上期")
    exists = db.scalar(
        select(UtilityBill).where(
            UtilityBill.room_id == room.id,
            UtilityBill.bill_month == payload.bill_month,
        )
    )
    if exists:
        raise HTTPException(status_code=400, detail="该房间本月账单已存在")

    bill = UtilityBill(
        bill_no=make_no("B"),
        room_id=room.id,
        bill_month=payload.bill_month,
        water_prev=payload.water_prev,
        water_curr=payload.water_curr,
        water_unit_price=payload.water_unit_price,
        electricity_prev=payload.electricity_prev,
        electricity_curr=payload.electricity_curr,
        electricity_unit_price=payload.electricity_unit_price,
        status="unpaid",
        due_date=payload.due_date,
        generated_by=user.id,
        remark=payload.remark,
    )
    db.add(bill)
    commit_or_400(db)
    db.refresh(bill)
    for user_id in _room_user_ids(db, room.id):
        notify(
            db,
            user_id,
            "utility",
            "新的水电账单",
            f"{room.room_no} 房间 {payload.bill_month:%Y-%m} 账单已生成",
            "utility_bill",
            bill.id,
        )
    db.commit()
    return BillOut.model_validate(bill_dict(db, bill))


@router.post("/bills/{bill_id}/pay", response_model=BillOut, summary="余额缴纳水电账单")
def pay_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BillOut:
    bill = db.get(UtilityBill, bill_id)
    if bill is None:
        raise HTTPException(status_code=404, detail="账单不存在")
    account = db.scalar(
        select(UtilityAccount).where(UtilityAccount.room_id == bill.room_id).with_for_update()
    )
    if account is None:
        raise HTTPException(status_code=404, detail="该房间尚未建立水电账户")
    _ensure_account_access(db, user, account)
    if bill.status != "unpaid":
        raise HTTPException(status_code=400, detail="该账单当前不能缴费")
    if account.balance < bill.total_amount:
        raise HTTPException(status_code=400, detail="余额不足，请先充值")

    account.balance = account.balance - bill.total_amount
    tx = UtilityTransaction(
        account_id=account.id,
        type="bill_payment",
        amount=-bill.total_amount,
        balance_after=account.balance,
        biz_type="utility_bill",
        biz_id=bill.id,
        created_by=user.id,
        remark=f"缴纳 {bill.bill_month:%Y-%m} 水电费",
    )
    db.add(tx)
    bill.status = "paid"
    bill.paid_at = datetime.now()
    for user_id in _room_user_ids(db, bill.room_id):
        notify(db, user_id, "utility", "水电账单已缴费", f"账单 {bill.bill_no} 已缴费", "utility_bill", bill.id)
    commit_or_400(db)
    db.refresh(bill)
    return BillOut.model_validate(bill_dict(db, bill))


@router.get("/recharges", response_model=Page[RechargeOut], summary="充值订单列表")
def list_recharges(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[RechargeOut]:
    stmt = select(RechargeOrder).order_by(RechargeOrder.id.desc())
    if user.role == "student":
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        current_room = current_room_id_for_student(db, student.id) if student else None
        account = db.scalar(select(UtilityAccount).where(UtilityAccount.room_id == current_room)) if current_room else None
        if account is None:
            return Page(items=[], total=0, page=page, page_size=page_size)
        stmt = stmt.where(RechargeOrder.account_id == account.id)
    else:
        allowed = building_ids_for_user(db, user)
        if allowed is not None:
            if not allowed:
                return Page(items=[], total=0, page=page, page_size=page_size)
            room_ids = select(Room.id).where(Room.building_id.in_(allowed))
            account_ids = select(UtilityAccount.id).where(UtilityAccount.room_id.in_(room_ids))
            stmt = stmt.where(RechargeOrder.account_id.in_(account_ids))
    if status:
        stmt = stmt.where(RechargeOrder.status == status)

    rows, total = paginate(db, stmt, page, page_size)
    return Page(
        items=[RechargeOut.model_validate(recharge_dict(db, x)) for x in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/recharges", response_model=RechargeOut, summary="创建模拟充值订单")
def create_recharge(
    payload: RechargeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RechargeOut:
    account = db.get(UtilityAccount, payload.account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="水电账户不存在")
    if account.status != "active":
        raise HTTPException(status_code=400, detail="水电账户已冻结")
    _ensure_account_access(db, user, account)
    order = RechargeOrder(
        order_no=make_no("C"),
        account_id=account.id,
        amount=payload.amount,
        pay_method=payload.pay_method,
        status="pending",
        created_by=user.id,
        remark=payload.remark,
    )
    db.add(order)
    commit_or_400(db)
    db.refresh(order)
    return RechargeOut.model_validate(recharge_dict(db, order))


@router.post("/recharges/{order_id}/pay", response_model=RechargeOut, summary="模拟支付充值订单")
def pay_recharge(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RechargeOut:
    order = db.get(RechargeOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="充值订单不存在")
    account = db.scalar(
        select(UtilityAccount).where(UtilityAccount.id == order.account_id).with_for_update()
    )
    if account is None:
        raise HTTPException(status_code=404, detail="水电账户不存在")
    _ensure_account_access(db, user, account)
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="该订单当前不能支付")

    account.balance = account.balance + order.amount
    tx = UtilityTransaction(
        account_id=account.id,
        type="recharge",
        amount=order.amount,
        balance_after=account.balance,
        biz_type="recharge_order",
        biz_id=order.id,
        created_by=user.id,
        remark="模拟充值",
    )
    db.add(tx)
    order.status = "success"
    order.paid_at = datetime.now()
    notify(
        db,
        user.id,
        "utility",
        "充值成功",
        f"充值 {order.amount} 元已到账，当前余额 {account.balance} 元",
        "recharge_order",
        order.id,
    )
    commit_or_400(db)
    db.refresh(order)
    return RechargeOut.model_validate(recharge_dict(db, order))
