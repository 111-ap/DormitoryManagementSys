from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.deps import (
    building_ids_for_user,
    current_room_id_for_student,
    get_current_user,
)
from app.db.session import get_db
from app.models import Notice, Room, Student, User
from app.schemas import Message, NoticeCreate, NoticeOut, Page
from app.services.common import commit_or_400, paginate
from app.services.notifications import notify
from app.services.serializers import notice_dict

router = APIRouter(prefix="/notices", tags=["公告"])


@router.get("", response_model=Page[NoticeOut], summary="公告列表")
def list_notices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    building_id: int | None = None,
    room_id: int | None = None,
    scope: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[NoticeOut]:
    stmt = select(Notice).where(Notice.status == "published").order_by(Notice.published_at.desc())
    if user.role == "student":
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        if student is None:
            return Page(items=[], total=0, page=page, page_size=page_size)
        current_room = current_room_id_for_student(db, student.id)
        room = db.get(Room, current_room) if current_room else None
        if room is None:
            return Page(items=[], total=0, page=page, page_size=page_size)
        stmt = stmt.where(
            or_(
                and_(Notice.scope == "building", Notice.building_id == room.building_id),
                and_(Notice.scope == "room", Notice.room_id == room.id),
            )
        )
    else:
        allowed = building_ids_for_user(db, user)
        if allowed is not None:
            if not allowed:
                return Page(items=[], total=0, page=page, page_size=page_size)
            stmt = stmt.where(Notice.building_id.in_(allowed))
    if building_id is not None:
        stmt = stmt.where(Notice.building_id == building_id)
    if room_id is not None:
        stmt = stmt.where(Notice.room_id == room_id)
    if scope:
        stmt = stmt.where(Notice.scope == scope)

    rows, total = paginate(db, stmt, page, page_size)
    return Page(
        items=[NoticeOut.model_validate(notice_dict(db, x)) for x in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=NoticeOut, summary="发布公告")
def create_notice(
    payload: NoticeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NoticeOut:
    building_id = payload.building_id
    room_id = payload.room_id
    scope = payload.scope

    if user.role == "student":
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        if student is None or not student.is_dorm_leader:
            raise HTTPException(status_code=403, detail="只有舍长可以发布寝室公告")
        current_room = current_room_id_for_student(db, student.id)
        if current_room is None:
            raise HTTPException(status_code=400, detail="当前没有在住房间")
        room = db.get(Room, current_room)
        if room is None:
            raise HTTPException(status_code=404, detail="房间不存在")
        scope = "room"
        building_id = room.building_id
        room_id = room.id
    elif user.role == "building_admin":
        allowed = building_ids_for_user(db, user)
        if not allowed:
            raise HTTPException(status_code=403, detail="尚未分配负责楼栋")
        building_id = next(iter(allowed))
        scope = "building"
        room_id = None
    elif user.role != "sys_admin":
        raise HTTPException(status_code=403, detail="无权发布公告")

    if building_id is None:
        raise HTTPException(status_code=400, detail="请选择楼栋")
    if scope == "building":
        room_id = None
    elif room_id is None:
        raise HTTPException(status_code=400, detail="寝室公告必须指定房间")

    room = db.get(Room, room_id) if room_id else None
    if room_id and room is None:
        raise HTTPException(status_code=404, detail="房间不存在")
    if room and room.building_id != building_id:
        raise HTTPException(status_code=400, detail="房间不属于该楼栋")

    item = Notice(
        building_id=building_id,
        room_id=room_id,
        author_id=user.id,
        title=payload.title,
        content=payload.content,
        scope=scope,
        status="published",
    )
    db.add(item)
    commit_or_400(db)
    db.refresh(item)

    # 通知接收人：楼栋公告发给全楼学生，寝室公告发给本寝室学生
    if room_id:
        from app.models import RoomAssignment

        recipients = db.scalars(
            select(Student.user_id)
            .join(RoomAssignment, RoomAssignment.student_id == Student.id)
            .where(
                RoomAssignment.room_id == room_id,
                RoomAssignment.check_out_at.is_(None),
                Student.user_id.is_not(None),
            )
        ).all()
    else:
        from app.models import RoomAssignment

        room_ids = select(Room.id).where(Room.building_id == building_id)
        recipients = db.scalars(
            select(Student.user_id)
            .join(RoomAssignment, RoomAssignment.student_id == Student.id)
            .where(
                RoomAssignment.room_id.in_(room_ids),
                RoomAssignment.check_out_at.is_(None),
                Student.user_id.is_not(None),
            )
        ).all()
    for user_id in set(x for x in recipients if x):
        notify(db, user_id, "notice", "新的寝室公告", item.title, "notice", item.id)
    db.commit()
    return NoticeOut.model_validate(notice_dict(db, item))


@router.post("/{notice_id}/archive", response_model=Message, summary="归档公告")
def archive_notice(
    notice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Message:
    item = db.get(Notice, notice_id)
    if item is None:
        raise HTTPException(status_code=404, detail="公告不存在")
    if user.role != "sys_admin" and item.author_id != user.id:
        raise HTTPException(status_code=403, detail="无权归档该公告")
    item.status = "archived"
    commit_or_400(db)
    return Message(message="公告已归档")
