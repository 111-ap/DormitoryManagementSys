from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Room, RoomAssignment, StaffBuilding, Student, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/token")

STAFF_ROLES = {"sys_admin", "building_admin", "worker"}


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登录状态无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", 0))
    except (jwt.PyJWTError, ValueError, TypeError):
        raise credentials_error

    user = db.get(User, user_id)
    if user is None:
        raise credentials_error
    if user.status != "active":
        raise HTTPException(status_code=403, detail="账号已被禁用")
    return user


def require_roles(*roles: str) -> Callable:
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="没有权限执行该操作")
        return user

    return checker


def get_current_student(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Student:
    if user.role != "student":
        raise HTTPException(status_code=403, detail="仅学生账号可执行该操作")
    student = db.scalar(select(Student).where(Student.user_id == user.id))
    if student is None:
        raise HTTPException(status_code=404, detail="学生档案不存在")
    return student


def current_room_id_for_student(db: Session, student_id: int) -> int | None:
    return db.scalar(
        select(RoomAssignment.room_id)
        .where(
            RoomAssignment.student_id == student_id,
            RoomAssignment.check_out_at.is_(None),
        )
        .limit(1)
    )


def building_ids_for_user(db: Session, user: User) -> set[int] | None:
    """返回用户可访问的楼栋集合；None 表示全部楼栋。"""
    if user.role == "sys_admin":
        return None
    if user.role == "student":
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        if student is None:
            return set()
        room_id = current_room_id_for_student(db, student.id)
        if room_id is None:
            return set()
        building_id = db.scalar(select(Room.building_id).where(Room.id == room_id))
        return {building_id} if building_id else set()
    rows = db.scalars(
        select(StaffBuilding.building_id).where(StaffBuilding.user_id == user.id)
    ).all()
    return set(rows)


def ensure_building_access(db: Session, user: User, building_id: int) -> None:
    allowed = building_ids_for_user(db, user)
    if allowed is not None and building_id not in allowed:
        raise HTTPException(status_code=403, detail="无权访问该楼栋")


def ensure_room_access(db: Session, user: User, room_id: int) -> Room:
    room = db.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="房间不存在")
    ensure_building_access(db, user, room.building_id)
    return room


def ensure_staff(user: User) -> None:
    if user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="该操作仅限宿舍管理人员")
