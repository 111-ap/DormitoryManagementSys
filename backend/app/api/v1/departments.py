from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import Department, User
from app.schemas import DepartmentCreate, DepartmentOut
from app.services.common import commit_or_400

router = APIRouter(prefix="/departments", tags=["院系"])
admin_only = require_roles("sys_admin")


@router.get("", response_model=list[DepartmentOut], summary="院系列表")
def list_departments(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DepartmentOut]:
    rows = db.scalars(select(Department).order_by(Department.id)).all()
    return [DepartmentOut.model_validate(x) for x in rows]


@router.post("", response_model=DepartmentOut, summary="新建院系")
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> DepartmentOut:
    if db.scalar(select(Department).where(Department.code == payload.code)):
        raise HTTPException(status_code=400, detail="院系编码已存在")
    item = Department(**payload.model_dump())
    db.add(item)
    commit_or_400(db)
    db.refresh(item)
    return DepartmentOut.model_validate(item)


@router.patch("/{department_id}", response_model=DepartmentOut, summary="修改院系")
def update_department(
    department_id: int,
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> DepartmentOut:
    item = db.get(Department, department_id)
    if item is None:
        raise HTTPException(status_code=404, detail="院系不存在")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    commit_or_400(db)
    db.refresh(item)
    return DepartmentOut.model_validate(item)
