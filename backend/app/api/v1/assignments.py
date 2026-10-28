from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import building_ids_for_user, ensure_room_access, get_current_user, require_roles
from app.db.session import get_db
from app.models import Room, RoomAssignment, Student, User
from app.schemas import (
    AssignmentCreate,
    AssignmentOut,
    Message,
    Page,
    TransferRequest,
)
from app.services.common import commit_or_400, paginate
from app.services.notifications import notify
from app.services.serializers import assignment_dict

router = APIRouter(prefix="/assignments", tags=["住宿管理"])
staff_only = require_roles("sys_admin", "building_admin")


def _check_student_room(
    db: Session,
    student: Student,
    room: Room,
    exclude_assignment_id: int | None = None,
) -> None:
    if room.status != "normal":
        raise HTTPException(status_code=400, detail="房间当前不可分配")
    if room.gender != "mixed" and student.gender != room.gender:
        raise HTTPException(status_code=400, detail="学生性别与房间限制不一致")

    stmt = select(func.count(RoomAssignment.id)).where(
        RoomAssignment.room_id == room.id,
        RoomAssignment.check_out_at.is_(None),
    )
    if exclude_assignment_id is not None:
        stmt = stmt.where(RoomAssignment.id != exclude_assignment_id)
    occupied = db.scalar(stmt) or 0
    if occupied >= room.capacity:
        raise HTTPException(status_code=400, detail="房间已满")


def _check_bed_free(db: Session, room_id: int, bed_no: str, exclude_id: int | None = None) -> None:
    stmt = select(RoomAssignment.id).where(
        RoomAssignment.room_id == room_id,
        RoomAssignment.bed_no == bed_no,
        RoomAssignment.check_out_at.is_(None),
    )
    if exclude_id is not None:
        stmt = stmt.where(RoomAssignment.id != exclude_id)
    if db.scalar(stmt):
        raise HTTPException(status_code=400, detail="该床位已被占用")


@router.get("", response_model=Page[AssignmentOut], summary="住宿记录列表")
def list_assignments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: int | None = None,
    room_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[AssignmentOut]:
    stmt = select(RoomAssignment).order_by(RoomAssignment.id.desc())
    if user.role == "student":
        me = db.scalar(select(Student).where(Student.user_id == user.id))
        if me is None:
            return Page(items=[], total=0, page=page, page_size=page_size)
        stmt = stmt.where(RoomAssignment.student_id == me.id)
    else:
        allowed = building_ids_for_user(db, user)
        if allowed is not None:
            room_ids = select(Room.id).where(Room.building_id.in_(allowed))
            stmt = stmt.where(RoomAssignment.room_id.in_(room_ids))
    if student_id is not None:
        stmt = stmt.where(RoomAssignment.student_id == student_id)
    if room_id is not None:
        stmt = stmt.where(RoomAssignment.room_id == room_id)
    if status:
        stmt = stmt.where(RoomAssignment.status == status)

    rows, total = paginate(db, stmt, page, page_size)
    return Page(
        items=[AssignmentOut.model_validate(assignment_dict(db, x)) for x in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/me", response_model=AssignmentOut | None, summary="我的当前住宿")
def my_assignment(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AssignmentOut | None:
    if user.role != "student":
        raise HTTPException(status_code=403, detail="仅学生可查看自己的住宿")
    student = db.scalar(select(Student).where(Student.user_id == user.id))
    if student is None:
        return None
    item = db.scalar(
        select(RoomAssignment).where(
            RoomAssignment.student_id == student.id,
            RoomAssignment.check_out_at.is_(None),
        )
    )
    return AssignmentOut.model_validate(assignment_dict(db, item)) if item else None


@router.post("", response_model=AssignmentOut, summary="分配宿舍")
def assign_room(
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> AssignmentOut:
    room = ensure_room_access(db, user, payload.room_id)
    student = db.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")

    current = db.scalar(
        select(RoomAssignment).where(
            RoomAssignment.student_id == student.id,
            RoomAssignment.check_out_at.is_(None),
        )
    )
    if current is not None:
        raise HTTPException(status_code=400, detail="该学生已有当前住宿记录，请使用调宿")
    _check_student_room(db, student, room)
    _check_bed_free(db, room.id, payload.bed_no)

    item = RoomAssignment(
        student_id=student.id,
        room_id=room.id,
        bed_no=payload.bed_no,
        check_in_at=payload.check_in_at or datetime.now(),
        status="active",
        remark=payload.remark,
    )
    db.add(item)
    if student.user_id:
        notify(
            db,
            student.user_id,
            "assignment",
            "宿舍分配通知",
            f"你已被分配到 {room.room_no} 房间 {payload.bed_no} 床位",
            "room_assignment",
            None,
        )
    commit_or_400(db, "分房失败：床位或学生住宿状态冲突")
    db.refresh(item)
    return AssignmentOut.model_validate(assignment_dict(db, item))


@router.post("/{assignment_id}/transfer", response_model=AssignmentOut, summary="调宿")
def transfer_room(
    assignment_id: int,
    payload: TransferRequest,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> AssignmentOut:
    old = db.get(RoomAssignment, assignment_id)
    if old is None or old.check_out_at is not None:
        raise HTTPException(status_code=404, detail="当前住宿记录不存在")
    old_room = db.get(Room, old.room_id)
    if old_room is None:
        raise HTTPException(status_code=404, detail="原房间不存在")
    if user.role != "sys_admin":
        allowed = building_ids_for_user(db, user)
        if allowed is not None and old_room.building_id not in allowed:
            raise HTTPException(status_code=403, detail="无权操作该学生")
    new_room = ensure_room_access(db, user, payload.new_room_id)
    student = db.get(Student, old.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")

    _check_student_room(db, student, new_room, exclude_assignment_id=old.id)
    _check_bed_free(db, new_room.id, payload.new_bed_no, exclude_id=old.id)

    now = datetime.now()
    old.check_out_at = now
    old.status = "checked_out"
    old.remark = payload.reason or old.remark
    item = RoomAssignment(
        student_id=student.id,
        room_id=new_room.id,
        bed_no=payload.new_bed_no,
        check_in_at=now,
        status="active",
        remark=payload.reason,
    )
    db.add(item)
    if student.user_id:
        notify(
            db,
            student.user_id,
            "assignment",
            "调宿通知",
            f"你已调整到 {new_room.room_no} 房间 {payload.new_bed_no} 床位",
            "room_assignment",
            None,
        )
    commit_or_400(db, "调宿失败：目标床位或房间状态冲突")
    db.refresh(item)
    return AssignmentOut.model_validate(assignment_dict(db, item))


@router.post("/{assignment_id}/checkout", response_model=Message, summary="退宿")
def checkout(
    assignment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> Message:
    item = db.get(RoomAssignment, assignment_id)
    if item is None or item.check_out_at is not None:
        raise HTTPException(status_code=404, detail="当前住宿记录不存在")
    room = db.get(Room, item.room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="房间不存在")
    if user.role != "sys_admin":
        allowed = building_ids_for_user(db, user)
        if allowed is not None and room.building_id not in allowed:
            raise HTTPException(status_code=403, detail="无权操作该学生")

    item.check_out_at = datetime.now()
    item.status = "checked_out"
    student = db.get(Student, item.student_id)
    if student and student.user_id:
        notify(
            db,
            student.user_id,
            "assignment",
            "退宿通知",
            f"你已退宿 {room.room_no} 房间",
            "room_assignment",
            item.id,
        )
    commit_or_400(db)
    return Message(message="退宿成功")
