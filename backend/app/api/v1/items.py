from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import (
    building_ids_for_user,
    current_room_id_for_student,
    get_current_student,
    get_current_user,
    require_roles,
)
from app.db.session import get_db
from app.models import ItemRecord, Room, Student, User
from app.schemas import ItemCreate, ItemOut, ItemReview, Message, Page
from app.services.common import commit_or_400, paginate
from app.services.notifications import notify
from app.services.serializers import item_dict

router = APIRouter(prefix="/items", tags=["物品出入"])
reviewer_only = require_roles("sys_admin", "building_admin")


@router.get("", response_model=Page[ItemOut], summary="物品出入记录")
def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    direction: str | None = None,
    room_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[ItemOut]:
    stmt = select(ItemRecord).order_by(ItemRecord.id.desc())
    if user.role == "student":
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        if student is None:
            return Page(items=[], total=0, page=page, page_size=page_size)
        stmt = stmt.where(ItemRecord.student_id == student.id)
    else:
        allowed = building_ids_for_user(db, user)
        if allowed is not None:
            if not allowed:
                return Page(items=[], total=0, page=page, page_size=page_size)
            room_ids = select(Room.id).where(Room.building_id.in_(allowed))
            stmt = stmt.where(ItemRecord.room_id.in_(room_ids))
    if status:
        stmt = stmt.where(ItemRecord.status == status)
    if direction:
        stmt = stmt.where(ItemRecord.direction == direction)
    if room_id is not None:
        stmt = stmt.where(ItemRecord.room_id == room_id)

    rows, total = paginate(db, stmt, page, page_size)
    return Page(
        items=[ItemOut.model_validate(item_dict(db, x)) for x in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ItemOut, summary="登记物品出入")
def create_item(
    payload: ItemCreate,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> ItemOut:
    room_id = current_room_id_for_student(db, student.id)
    if room_id is None:
        raise HTTPException(status_code=400, detail="当前没有在住房间")
    item = ItemRecord(
        room_id=room_id,
        student_id=student.id,
        item_name=payload.item_name,
        quantity=payload.quantity,
        unit=payload.unit,
        direction=payload.direction,
        occurred_at=payload.occurred_at or datetime.now(),
        reason=payload.reason,
        status="pending",
    )
    db.add(item)
    commit_or_400(db)
    db.refresh(item)
    return ItemOut.model_validate(item_dict(db, item))


@router.post("/{item_id}/review", response_model=ItemOut, summary="审核物品出入")
def review_item(
    item_id: int,
    payload: ItemReview,
    db: Session = Depends(get_db),
    user: User = Depends(reviewer_only),
) -> ItemOut:
    item = db.get(ItemRecord, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="物品出入记录不存在")
    room = db.get(Room, item.room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="房间不存在")
    allowed = building_ids_for_user(db, user)
    if allowed is not None and room.building_id not in allowed:
        raise HTTPException(status_code=403, detail="无权审核该记录")
    if item.status != "pending":
        raise HTTPException(status_code=400, detail="该记录已审核")

    item.status = payload.status
    item.reviewed_by = user.id
    item.reviewed_at = datetime.now()
    item.review_remark = payload.remark
    student = db.get(Student, item.student_id)
    if student and student.user_id:
        notify(
            db,
            student.user_id,
            "item",
            "物品出入审核结果",
            f"{item.item_name} 的登记已被{'通过' if payload.status == 'approved' else '驳回'}",
            "item_record",
            item.id,
        )
    commit_or_400(db)
    db.refresh(item)
    return ItemOut.model_validate(item_dict(db, item))
