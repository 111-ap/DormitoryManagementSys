from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import (
    building_ids_for_user,
    ensure_building_access,
    get_current_user,
    require_roles,
)
from app.db.session import get_db
from app.models import Building, Room, User
from app.schemas import Page, RoomCreate, RoomOut, RoomUpdate
from app.services.common import commit_or_400, paginate
from app.services.serializers import room_dict

router = APIRouter(prefix="/rooms", tags=["房间"])
staff_only = require_roles("sys_admin", "building_admin")


@router.get("", response_model=Page[RoomOut], summary="可见房间列表")
def list_rooms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    building_id: int | None = None,
    keyword: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[RoomOut]:
    allowed = building_ids_for_user(db, user)
    stmt = select(Room).order_by(Room.building_id, Room.room_no)
    if allowed is not None:
        if not allowed:
            return Page(items=[], total=0, page=page, page_size=page_size)
        stmt = stmt.where(Room.building_id.in_(allowed))
    if building_id is not None:
        if allowed is not None and building_id not in allowed:
            raise HTTPException(status_code=403, detail="无权访问该楼栋")
        stmt = stmt.where(Room.building_id == building_id)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where((Room.room_no.like(like)) | (Room.phone.like(like)))
    if status:
        stmt = stmt.where(Room.status == status)

    rows, total = paginate(db, stmt, page, page_size)
    return Page(
        items=[RoomOut.model_validate(room_dict(db, x)) for x in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{room_id}", response_model=RoomOut, summary="房间详情")
def get_room(
    room_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RoomOut:
    room = db.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="房间不存在")
    allowed = building_ids_for_user(db, user)
    if allowed is not None and room.building_id not in allowed:
        raise HTTPException(status_code=403, detail="无权访问该房间")
    return RoomOut.model_validate(room_dict(db, room))


@router.post("", response_model=RoomOut, summary="新建房间")
def create_room(
    payload: RoomCreate,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> RoomOut:
    ensure_building_access(db, user, payload.building_id)
    building = db.get(Building, payload.building_id)
    if building is None:
        raise HTTPException(status_code=404, detail="楼栋不存在")
    exists = db.scalar(
        select(Room).where(
            Room.building_id == payload.building_id,
            Room.room_no == payload.room_no,
        )
    )
    if exists:
        raise HTTPException(status_code=400, detail="该楼栋下房间号已存在")
    item = Room(**payload.model_dump())
    db.add(item)
    commit_or_400(db)
    db.refresh(item)
    return RoomOut.model_validate(room_dict(db, item))


@router.patch("/{room_id}", response_model=RoomOut, summary="修改房间")
def update_room(
    room_id: int,
    payload: RoomUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> RoomOut:
    room = db.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="房间不存在")
    ensure_building_access(db, user, room.building_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(room, key, value)
    commit_or_400(db)
    db.refresh(room)
    return RoomOut.model_validate(room_dict(db, room))
