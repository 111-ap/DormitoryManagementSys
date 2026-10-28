from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import building_ids_for_user, get_current_user, require_roles
from app.db.session import get_db
from app.models import Building, User
from app.schemas import BuildingCreate, BuildingOut, Page
from app.services.common import commit_or_400, paginate

router = APIRouter(prefix="/buildings", tags=["楼栋"])
admin_only = require_roles("sys_admin")


@router.get("", response_model=Page[BuildingOut], summary="可见楼栋列表")
def list_buildings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[BuildingOut]:
    allowed = building_ids_for_user(db, user)
    stmt = select(Building).order_by(Building.id)
    if allowed is not None:
        if not allowed:
            return Page(items=[], total=0, page=page, page_size=page_size)
        stmt = stmt.where(Building.id.in_(allowed))
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where((Building.name.like(like)) | (Building.code.like(like)))
    rows, total = paginate(db, stmt, page, page_size)
    return Page(items=[BuildingOut.model_validate(x) for x in rows], total=total, page=page, page_size=page_size)


@router.get("/{building_id}", response_model=BuildingOut, summary="楼栋详情")
def get_building(
    building_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BuildingOut:
    allowed = building_ids_for_user(db, user)
    if allowed is not None and building_id not in allowed:
        raise HTTPException(status_code=403, detail="无权访问该楼栋")
    item = db.get(Building, building_id)
    if item is None:
        raise HTTPException(status_code=404, detail="楼栋不存在")
    return BuildingOut.model_validate(item)


@router.post("", response_model=BuildingOut, summary="新建楼栋")
def create_building(
    payload: BuildingCreate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> BuildingOut:
    if db.scalar(select(Building).where(Building.code == payload.code)):
        raise HTTPException(status_code=400, detail="楼栋编码已存在")
    item = Building(**payload.model_dump())
    db.add(item)
    commit_or_400(db)
    db.refresh(item)
    return BuildingOut.model_validate(item)


@router.patch("/{building_id}", response_model=BuildingOut, summary="修改楼栋")
def update_building(
    building_id: int,
    payload: BuildingCreate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> BuildingOut:
    item = db.get(Building, building_id)
    if item is None:
        raise HTTPException(status_code=404, detail="楼栋不存在")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    commit_or_400(db)
    db.refresh(item)
    return BuildingOut.model_validate(item)
