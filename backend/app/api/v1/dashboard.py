from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import building_ids_for_user, current_room_id_for_student, get_current_user
from app.db.session import get_db
from app.models import (
    Building,
    Notification,
    RepairOrder,
    Room,
    RoomAssignment,
    Student,
    User,
    UtilityAccount,
    UtilityBill,
)

router = APIRouter(prefix="/dashboard", tags=["首页统计"])


@router.get("", summary="首页统计")
def dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    allowed = building_ids_for_user(db, user)

    if user.role == "student":
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        current_room = current_room_id_for_student(db, student.id) if student else None
        account = db.scalar(select(UtilityAccount).where(UtilityAccount.room_id == current_room)) if current_room else None
        unpaid = db.scalar(
            select(func.count(UtilityBill.id)).where(
                UtilityBill.room_id == current_room,
                UtilityBill.status == "unpaid",
            )
        ) if current_room else 0
        repairs = db.scalar(
            select(func.count(RepairOrder.id)).where(
                RepairOrder.reporter_id == user.id,
                RepairOrder.status.in_(["pending", "processing"]),
            )
        ) or 0
        unread = db.scalar(
            select(func.count(Notification.id)).where(
                Notification.user_id == user.id,
                Notification.is_read.is_(False),
            )
        ) or 0
        return {
            "role": user.role,
            "room_id": current_room,
            "balance": str(account.balance) if account else "0.00",
            "unpaid_bills": int(unpaid or 0),
            "open_repairs": int(repairs),
            "unread_notifications": int(unread),
        }

    room_ids = select(Room.id)
    if allowed is not None:
        if not allowed:
            room_ids = select(Room.id).where(Room.id == -1)
        else:
            room_ids = select(Room.id).where(Room.building_id.in_(allowed))

    rooms_count = db.scalar(select(func.count(Room.id)).where(Room.id.in_(room_ids))) or 0
    active_students = db.scalar(
        select(func.count(RoomAssignment.id)).where(
            RoomAssignment.room_id.in_(room_ids),
            RoomAssignment.check_out_at.is_(None),
        )
    ) or 0
    pending_repairs = db.scalar(
        select(func.count(RepairOrder.id)).where(
            RepairOrder.room_id.in_(room_ids),
            RepairOrder.status.in_(["pending", "processing"]),
        )
    ) or 0
    unpaid_bills = db.scalar(
        select(func.count(UtilityBill.id)).where(
            UtilityBill.room_id.in_(room_ids),
            UtilityBill.status == "unpaid",
        )
    ) or 0
    total_balance = db.scalar(
        select(func.coalesce(func.sum(UtilityAccount.balance), 0)).where(
            UtilityAccount.room_id.in_(room_ids)
        )
    ) or 0
    buildings_count = (
        db.scalar(select(func.count(Building.id)))
        if allowed is None
        else len(allowed)
    )
    return {
        "role": user.role,
        "buildings": int(buildings_count or 0),
        "rooms": int(rooms_count),
        "active_students": int(active_students),
        "open_repairs": int(pending_repairs),
        "unpaid_bills": int(unpaid_bills),
        "utility_balance": str(total_balance),
    }
