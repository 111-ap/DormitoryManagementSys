from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import (
    building_ids_for_user,
    current_room_id_for_student,
    ensure_room_access,
    get_current_student,
    get_current_user,
)
from app.db.session import get_db
from app.models import Room, Student, User, Visitor
from app.schemas import Message, Page, VisitorCreate, VisitorOut
from app.services.common import commit_or_400, paginate
from app.services.serializers import visitor_dict

router = APIRouter(prefix="/visitors", tags=["访客"])


@router.get("", response_model=Page[VisitorOut], summary="访客记录列表")
def list_visitors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    room_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[VisitorOut]:
    stmt = select(Visitor).order_by(Visitor.id.desc())
    if user.role == "student":
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        if student is None:
            return Page(items=[], total=0, page=page, page_size=page_size)
        stmt = stmt.where(Visitor.host_student_id == student.id)
    else:
        allowed = building_ids_for_user(db, user)
        if allowed is not None:
            if not allowed:
                return Page(items=[], total=0, page=page, page_size=page_size)
            room_ids = select(Room.id).where(Room.building_id.in_(allowed))
            stmt = stmt.where(Visitor.room_id.in_(room_ids))
    if status:
        stmt = stmt.where(Visitor.status == status)
    if room_id is not None:
        stmt = stmt.where(Visitor.room_id == room_id)

    rows, total = paginate(db, stmt, page, page_size)
    return Page(
        items=[VisitorOut.model_validate(visitor_dict(db, x)) for x in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=VisitorOut, summary="登记访客")
def create_visitor(
    payload: VisitorCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> VisitorOut:
    host_student_id = payload.host_student_id
    room_id = payload.room_id

    if user.role == "student":
        me = db.scalar(select(Student).where(Student.user_id == user.id))
        if me is None:
            raise HTTPException(status_code=404, detail="学生档案不存在")
        current_room = current_room_id_for_student(db, me.id)
        if current_room is None:
            raise HTTPException(status_code=400, detail="当前没有在住房间")
        host_student_id = me.id
        room_id = current_room
    else:
        if host_student_id is None or room_id is None:
            raise HTTPException(status_code=400, detail="请选择被访学生和房间")
        ensure_room_access(db, user, room_id)

    host = db.get(Student, host_student_id)
    if host is None:
        raise HTTPException(status_code=404, detail="被访学生不存在")
    room = db.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="房间不存在")
    if user.role == "student" and room.id != current_room_id_for_student(db, host.id):
        raise HTTPException(status_code=400, detail="被访学生不在该房间")

    item = Visitor(
        visitor_name=payload.visitor_name,
        id_type=payload.id_type,
        id_no=payload.id_no,
        phone=payload.phone,
        host_student_id=host.id,
        room_id=room.id,
        visit_at=payload.visit_at or datetime.now(),
        reason=payload.reason,
        status="visiting",
        registered_by=user.id,
        remark=payload.remark,
    )
    db.add(item)
    commit_or_400(db)
    db.refresh(item)
    return VisitorOut.model_validate(visitor_dict(db, item))


@router.post("/{visitor_id}/leave", response_model=Message, summary="访客离开")
def leave_visitor(
    visitor_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Message:
    item = db.get(Visitor, visitor_id)
    if item is None:
        raise HTTPException(status_code=404, detail="访客记录不存在")
    if user.role == "student":
        me = db.scalar(select(Student).where(Student.user_id == user.id))
        if me is None or item.host_student_id != me.id:
            raise HTTPException(status_code=403, detail="无权操作该访客记录")
    else:
        allowed = building_ids_for_user(db, user)
        room = db.get(Room, item.room_id)
        if allowed is not None and room and room.building_id not in allowed:
            raise HTTPException(status_code=403, detail="无权操作该访客记录")
    if item.status != "visiting":
        raise HTTPException(status_code=400, detail="该访客当前不是来访状态")
    item.status = "left"
    item.leave_at = datetime.now()
    commit_or_400(db)
    return Message(message="访客已登记离开")


@router.post("/{visitor_id}/cancel", response_model=Message, summary="取消访客登记")
def cancel_visitor(
    visitor_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Message:
    item = db.get(Visitor, visitor_id)
    if item is None:
        raise HTTPException(status_code=404, detail="访客记录不存在")
    if user.role == "student":
        me = db.scalar(select(Student).where(Student.user_id == user.id))
        if me is None or item.host_student_id != me.id:
            raise HTTPException(status_code=403, detail="无权操作该访客记录")
    else:
        allowed = building_ids_for_user(db, user)
        room = db.get(Room, item.room_id)
        if allowed is not None and room and room.building_id not in allowed:
            raise HTTPException(status_code=403, detail="无权操作该访客记录")
    if item.status != "visiting":
        raise HTTPException(status_code=400, detail="该访客当前不能取消")
    item.status = "cancelled"
    commit_or_400(db)
    return Message(message="访客登记已取消")
