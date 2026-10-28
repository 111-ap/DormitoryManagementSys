from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.security import hash_password
from app.db.session import get_db
from app.models import Building, StaffBuilding, User
from app.schemas import (
    Message,
    Page,
    UserBuildingsUpdate,
    UserCreate,
    UserOut,
    UserUpdate,
)
from app.services.common import commit_or_400, paginate

router = APIRouter(prefix="/users", tags=["账号管理"])
admin_only = require_roles("sys_admin")


@router.get("", response_model=Page[UserOut], summary="用户列表")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    role: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> Page[UserOut]:
    stmt = select(User).order_by(User.id.desc())
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            (User.username.like(like))
            | (User.real_name.like(like))
            | (User.phone.like(like))
        )
    if role:
        stmt = stmt.where(User.role == role)
    rows, total = paginate(db, stmt, page, page_size)
    return Page(items=[UserOut.model_validate(x) for x in rows], total=total, page=page, page_size=page_size)


@router.post("", response_model=UserOut, summary="新建用户")
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> UserOut:
    exists = db.scalar(select(User).where(User.username == payload.username))
    if exists:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        real_name=payload.real_name,
        role=payload.role,
        phone=payload.phone,
        email=payload.email,
        status="active",
    )
    db.add(user)
    commit_or_400(db)
    db.refresh(user)
    return UserOut.model_validate(user)


@router.patch("/{user_id}", response_model=UserOut, summary="修改用户")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> UserOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    data = payload.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        user.password_hash = hash_password(data.pop("password"))
    for key, value in data.items():
        setattr(user, key, value)
    commit_or_400(db)
    db.refresh(user)
    return UserOut.model_validate(user)


@router.put("/{user_id}/buildings", response_model=Message, summary="设置员工负责楼栋")
def set_user_buildings(
    user_id: int,
    payload: UserBuildingsUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> Message:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.role not in {"building_admin", "worker"}:
        raise HTTPException(status_code=400, detail="只有楼管或水电工需要绑定楼栋")
    if user.role == "building_admin" and len(payload.building_ids) > 1:
        raise HTTPException(status_code=400, detail="一个楼管账号只能负责一栋楼")

    building_ids = list(dict.fromkeys(payload.building_ids))
    if building_ids:
        found = db.scalars(select(Building.id).where(Building.id.in_(building_ids))).all()
        if len(found) != len(building_ids):
            raise HTTPException(status_code=400, detail="存在无效楼栋ID")

    db.execute(delete(StaffBuilding).where(StaffBuilding.user_id == user_id))
    for building_id in building_ids:
        db.add(StaffBuilding(user_id=user_id, building_id=building_id))
    commit_or_400(db)
    return Message(message="楼栋负责关系已更新")
