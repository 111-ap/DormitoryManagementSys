import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.deps import (
    building_ids_for_user,
    get_current_student,
    get_current_user,
    require_roles,
)
from app.core.security import hash_password
from app.db.session import get_db
from app.models import Room, RoomAssignment, Student, User
from app.schemas import (
    Page,
    PasswordReset,
    PasswordResetOut,
    StudentCreate,
    StudentOut,
    StudentUpdate,
)
from app.services.common import commit_or_400, paginate
from app.services.serializers import student_dict

router = APIRouter(prefix="/students", tags=["学生"])
staff_only = require_roles("sys_admin", "building_admin", "worker")
student_writer = require_roles("sys_admin", "building_admin")


def _scoped_student_ids(db: Session, user: User):
    allowed = building_ids_for_user(db, user)
    if allowed is None:
        return None
    if not allowed:
        return select(Student.id).where(False)
    room_ids = select(Room.id).where(Room.building_id.in_(allowed))
    return select(RoomAssignment.student_id).where(
        RoomAssignment.room_id.in_(room_ids),
        RoomAssignment.check_out_at.is_(None),
    )


@router.get("", response_model=Page[StudentOut], summary="学生列表")
def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    department_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> Page[StudentOut]:
    stmt = select(Student).order_by(Student.id.desc())
    scoped = _scoped_student_ids(db, user)
    if scoped is not None:
        stmt = stmt.where(Student.id.in_(scoped))
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                Student.student_no.like(like),
                Student.name.like(like),
                Student.class_name.like(like),
            )
        )
    if department_id is not None:
        stmt = stmt.where(Student.department_id == department_id)
    if status:
        stmt = stmt.where(Student.status == status)

    rows, total = paginate(db, stmt, page, page_size)
    return Page(
        items=[StudentOut.model_validate(student_dict(db, x)) for x in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/me", response_model=StudentOut, summary="我的学生档案")
def my_student(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> StudentOut:
    return StudentOut.model_validate(student_dict(db, student))


@router.get("/{student_id}", response_model=StudentOut, summary="学生详情")
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StudentOut:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    if user.role == "student":
        me = db.scalar(select(Student).where(Student.user_id == user.id))
        if me is None or me.id != student.id:
            raise HTTPException(status_code=403, detail="无权访问该学生")
    else:
        allowed = building_ids_for_user(db, user)
        if allowed is not None:
            room_ids = select(Room.id).where(Room.building_id.in_(allowed))
            exists = db.scalar(
                select(RoomAssignment.id).where(
                    RoomAssignment.student_id == student.id,
                    RoomAssignment.room_id.in_(room_ids),
                    RoomAssignment.check_out_at.is_(None),
                )
            )
            if not exists:
                raise HTTPException(status_code=403, detail="无权访问该学生")
    return StudentOut.model_validate(student_dict(db, student))


@router.post("", response_model=StudentOut, summary="新建学生档案")
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(student_writer),
) -> StudentOut:
    if db.scalar(select(Student).where(Student.student_no == payload.student_no)):
        raise HTTPException(status_code=400, detail="学号已存在")
    if payload.user_id is not None:
        if db.scalar(select(Student).where(Student.user_id == payload.user_id)):
            raise HTTPException(status_code=400, detail="该账号已关联学生档案")
    item = Student(**payload.model_dump())
    db.add(item)
    commit_or_400(db)
    db.refresh(item)
    return StudentOut.model_validate(student_dict(db, item))


@router.post("/{student_id}/account", response_model=PasswordResetOut, summary="为学生创建登录账号")
def create_student_account(
    student_id: int,
    payload: PasswordReset,
    db: Session = Depends(get_db),
    user: User = Depends(student_writer),
) -> PasswordResetOut:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    if student.user_id is not None:
        raise HTTPException(status_code=400, detail="该学生已有登录账号")
    if user.role == "building_admin":
        allowed = building_ids_for_user(db, user)
        room_ids = select(Room.id).where(Room.building_id.in_(allowed or set()))
        exists = db.scalar(
            select(RoomAssignment.id).where(
                RoomAssignment.student_id == student.id,
                RoomAssignment.room_id.in_(room_ids),
                RoomAssignment.check_out_at.is_(None),
            )
        )
        if not exists:
            raise HTTPException(status_code=403, detail="无权为该学生创建账号")
    if db.scalar(select(User).where(User.username == student.student_no)):
        raise HTTPException(status_code=400, detail="学号已被其他账号使用")

    generated = payload.password is None
    password = payload.password or secrets.token_urlsafe(12)
    account = User(
        username=student.student_no,
        password_hash=hash_password(password),
        real_name=student.name,
        role="student",
        phone=student.phone,
        status="active",
    )
    db.add(account)
    db.flush()
    student.user_id = account.id
    commit_or_400(db)
    return PasswordResetOut(
        username=account.username,
        initial_password=password if generated else None,
    )


@router.patch("/{student_id}", response_model=StudentOut, summary="修改学生档案")
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(student_writer),
) -> StudentOut:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    if user.role == "building_admin":
        allowed = building_ids_for_user(db, user)
        room_ids = select(Room.id).where(Room.building_id.in_(allowed or set()))
        exists = db.scalar(
            select(RoomAssignment.id).where(
                RoomAssignment.student_id == student.id,
                RoomAssignment.room_id.in_(room_ids),
                RoomAssignment.check_out_at.is_(None),
            )
        )
        if not exists:
            raise HTTPException(status_code=403, detail="无权修改该学生")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, key, value)
    commit_or_400(db)
    db.refresh(student)
    return StudentOut.model_validate(student_dict(db, student))
