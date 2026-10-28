from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import (
    building_ids_for_user,
    ensure_room_access,
    get_current_student,
    get_current_user,
    require_roles,
)
from app.db.session import get_db
from app.models import Asset, Building, Room, RepairOrder, StaffBuilding, Student, User
from app.schemas import (
    Message,
    Page,
    RepairAccept,
    RepairCancel,
    RepairComplete,
    RepairCreate,
    RepairOut,
)
from app.services.common import commit_or_400, make_no, paginate
from app.services.notifications import notify
from app.services.serializers import repair_dict

router = APIRouter(prefix="/repairs", tags=["报修"])
staff_only = require_roles("sys_admin", "building_admin", "worker")


def _room_building_id(db: Session, room_id: int) -> int:
    room = db.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="房间不存在")
    return room.building_id


def _ensure_worker_building(db: Session, user: User, building_id: int) -> None:
    allowed = building_ids_for_user(db, user)
    if allowed is not None and building_id not in allowed:
        raise HTTPException(status_code=403, detail="无权处理该楼栋报修")


@router.get("", response_model=Page[RepairOut], summary="报修列表")
def list_repairs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    priority: str | None = None,
    room_id: int | None = None,
    handler_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[RepairOut]:
    stmt = select(RepairOrder).order_by(RepairOrder.id.desc())
    if user.role == "student":
        stmt = stmt.where(RepairOrder.reporter_id == user.id)
    else:
        allowed = building_ids_for_user(db, user)
        if allowed is not None:
            room_ids = select(Room.id).where(Room.building_id.in_(allowed))
            stmt = stmt.where(RepairOrder.room_id.in_(room_ids))
    if status:
        stmt = stmt.where(RepairOrder.status == status)
    if priority:
        stmt = stmt.where(RepairOrder.priority == priority)
    if room_id is not None:
        stmt = stmt.where(RepairOrder.room_id == room_id)
    if handler_id is not None:
        stmt = stmt.where(RepairOrder.handler_id == handler_id)

    rows, total = paginate(db, stmt, page, page_size)
    return Page(
        items=[RepairOut.model_validate(repair_dict(db, x)) for x in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{repair_id}", response_model=RepairOut, summary="报修详情")
def get_repair(
    repair_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RepairOut:
    order = db.get(RepairOrder, repair_id)
    if order is None:
        raise HTTPException(status_code=404, detail="报修单不存在")
    if user.role == "student" and order.reporter_id != user.id:
        raise HTTPException(status_code=403, detail="无权访问该报修单")
    if user.role != "student":
        allowed = building_ids_for_user(db, user)
        if allowed is not None and _room_building_id(db, order.room_id) not in allowed:
            raise HTTPException(status_code=403, detail="无权访问该报修单")
    return RepairOut.model_validate(repair_dict(db, order))


@router.post("", response_model=RepairOut, summary="提交报修")
def create_repair(
    payload: RepairCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RepairOut:
    room_id = payload.room_id
    if user.role == "student":
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        if student is None:
            raise HTTPException(status_code=404, detail="学生档案不存在")
        from app.core.deps import current_room_id_for_student

        current_room = current_room_id_for_student(db, student.id)
        if current_room is None:
            raise HTTPException(status_code=400, detail="当前没有在住房间，不能报修")
        if room_id is not None and room_id != current_room:
            raise HTTPException(status_code=403, detail="只能报修自己当前房间")
        room_id = current_room
    elif user.role not in {"sys_admin", "building_admin"}:
        raise HTTPException(status_code=403, detail="水电工不能代学生创建报修单")

    if room_id is None:
        raise HTTPException(status_code=400, detail="请选择报修房间")
    room = ensure_room_access(db, user, room_id)

    asset_name = payload.asset_name
    if payload.asset_id is not None:
        asset = db.get(Asset, payload.asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="资产不存在")
        if asset.room_id != room.id:
            raise HTTPException(status_code=400, detail="资产不属于该房间")
        asset_name = asset_name or asset.name
    if not asset_name:
        raise HTTPException(status_code=400, detail="请选择资产或填写资产名称")

    order = RepairOrder(
        order_no=make_no("R"),
        room_id=room.id,
        asset_id=payload.asset_id,
        asset_name=asset_name,
        reporter_id=user.id,
        description=payload.description,
        priority=payload.priority,
        status="pending",
    )
    db.add(order)
    commit_or_400(db)
    db.refresh(order)

    admin_ids = db.scalars(
        select(StaffBuilding.user_id).where(StaffBuilding.building_id == room.building_id)
    ).all()
    for admin_id in set(admin_ids):
        notify(
            db,
            admin_id,
            "repair",
            "新的报修单",
            f"{room.room_no} 房间提交了报修：{payload.description[:60]}",
            "repair_order",
            order.id,
        )
    db.commit()
    return RepairOut.model_validate(repair_dict(db, order))


@router.post("/{repair_id}/accept", response_model=RepairOut, summary="水电工接单")
def accept_repair(
    repair_id: int,
    payload: RepairAccept,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("worker", "sys_admin")),
) -> RepairOut:
    order = db.get(RepairOrder, repair_id)
    if order is None:
        raise HTTPException(status_code=404, detail="报修单不存在")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="该报修单当前不能接单")
    _ensure_worker_building(db, user, _room_building_id(db, order.room_id))

    order.handler_id = user.id
    order.status = "processing"
    order.accepted_at = datetime.now()
    notify(
        db,
        order.reporter_id,
        "repair",
        "报修已接单",
        "水电工已接单，正在处理",
        "repair_order",
        order.id,
    )
    commit_or_400(db)
    db.refresh(order)
    return RepairOut.model_validate(repair_dict(db, order))


@router.post("/{repair_id}/complete", response_model=RepairOut, summary="完成维修")
def complete_repair(
    repair_id: int,
    payload: RepairComplete,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("worker", "sys_admin")),
) -> RepairOut:
    order = db.get(RepairOrder, repair_id)
    if order is None:
        raise HTTPException(status_code=404, detail="报修单不存在")
    if order.status != "processing":
        raise HTTPException(status_code=400, detail="该报修单当前不能办结")
    _ensure_worker_building(db, user, _room_building_id(db, order.room_id))
    if user.role == "worker" and order.handler_id not in (None, user.id):
        raise HTTPException(status_code=403, detail="该报修单由其他水电工处理")

    order.status = "completed"
    order.solution = payload.solution
    order.resolved_at = payload.resolved_at or datetime.now()
    if order.handler_id is None:
        order.handler_id = user.id
    notify(
        db,
        order.reporter_id,
        "repair",
        "报修已办结",
        f"维修已完成：{payload.solution[:60]}",
        "repair_order",
        order.id,
    )
    commit_or_400(db)
    db.refresh(order)
    return RepairOut.model_validate(repair_dict(db, order))


@router.post("/{repair_id}/cancel", response_model=RepairOut, summary="取消报修")
def cancel_repair(
    repair_id: int,
    payload: RepairCancel,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RepairOut:
    order = db.get(RepairOrder, repair_id)
    if order is None:
        raise HTTPException(status_code=404, detail="报修单不存在")
    if order.status in {"completed", "cancelled"}:
        raise HTTPException(status_code=400, detail="该报修单不能取消")
    if user.role == "student" and order.reporter_id != user.id:
        raise HTTPException(status_code=403, detail="无权取消该报修单")
    if user.role not in {"student", "building_admin", "sys_admin"}:
        raise HTTPException(status_code=403, detail="无权取消该报修单")
    if user.role == "building_admin":
        allowed = building_ids_for_user(db, user)
        if allowed is not None and _room_building_id(db, order.room_id) not in allowed:
            raise HTTPException(status_code=403, detail="无权取消该报修单")

    order.status = "cancelled"
    order.cancel_reason = payload.reason
    notify(
        db,
        order.reporter_id,
        "repair",
        "报修已取消",
        payload.reason,
        "repair_order",
        order.id,
    )
    commit_or_400(db)
    db.refresh(order)
    return RepairOut.model_validate(repair_dict(db, order))
