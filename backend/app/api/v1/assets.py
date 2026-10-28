from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import building_ids_for_user, ensure_room_access, get_current_user, require_roles
from app.db.session import get_db
from app.models import Asset, AssetCategory, Room, User
from app.schemas import (
    AssetCategoryCreate,
    AssetCategoryOut,
    AssetCreate,
    AssetOut,
    AssetUpdate,
    Page,
)
from app.services.common import commit_or_400, paginate
from app.services.serializers import asset_dict

router = APIRouter(prefix="/assets", tags=["资产"])
staff_only = require_roles("sys_admin", "building_admin")


@router.get("/categories", response_model=list[AssetCategoryOut], summary="资产类别")
def list_categories(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AssetCategoryOut]:
    rows = db.scalars(select(AssetCategory).order_by(AssetCategory.id)).all()
    return [AssetCategoryOut.model_validate(x) for x in rows]


@router.post("/categories", response_model=AssetCategoryOut, summary="新建资产类别")
def create_category(
    payload: AssetCategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(staff_only),
) -> AssetCategoryOut:
    if db.scalar(select(AssetCategory).where(AssetCategory.code == payload.code)):
        raise HTTPException(status_code=400, detail="资产类别编码已存在")
    item = AssetCategory(**payload.model_dump())
    db.add(item)
    commit_or_400(db)
    db.refresh(item)
    return AssetCategoryOut.model_validate(item)


@router.get("", response_model=Page[AssetOut], summary="资产列表")
def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    room_id: int | None = None,
    category_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[AssetOut]:
    stmt = select(Asset).order_by(Asset.id.desc())
    allowed = building_ids_for_user(db, user)
    if allowed is not None:
        if not allowed:
            return Page(items=[], total=0, page=page, page_size=page_size)
        room_ids = select(Room.id).where(Room.building_id.in_(allowed))
        stmt = stmt.where(Asset.room_id.in_(room_ids))
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where((Asset.asset_no.like(like)) | (Asset.name.like(like)))
    if room_id is not None:
        stmt = stmt.where(Asset.room_id == room_id)
    if category_id is not None:
        stmt = stmt.where(Asset.category_id == category_id)
    if status:
        stmt = stmt.where(Asset.status == status)

    rows, total = paginate(db, stmt, page, page_size)
    return Page(
        items=[AssetOut.model_validate(asset_dict(db, x)) for x in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{asset_id}", response_model=AssetOut, summary="资产详情")
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AssetOut:
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="资产不存在")
    room = db.get(Room, asset.room_id)
    allowed = building_ids_for_user(db, user)
    if allowed is not None and room and room.building_id not in allowed:
        raise HTTPException(status_code=403, detail="无权访问该资产")
    return AssetOut.model_validate(asset_dict(db, asset))


@router.post("", response_model=AssetOut, summary="新增资产")
def create_asset(
    payload: AssetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> AssetOut:
    ensure_room_access(db, user, payload.room_id)
    if db.scalar(select(Asset).where(Asset.asset_no == payload.asset_no)):
        raise HTTPException(status_code=400, detail="资产编号已存在")
    if db.get(AssetCategory, payload.category_id) is None:
        raise HTTPException(status_code=404, detail="资产类别不存在")
    item = Asset(**payload.model_dump())
    db.add(item)
    commit_or_400(db)
    db.refresh(item)
    return AssetOut.model_validate(asset_dict(db, item))


@router.patch("/{asset_id}", response_model=AssetOut, summary="修改资产")
def update_asset(
    asset_id: int,
    payload: AssetUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> AssetOut:
    item = db.get(Asset, asset_id)
    if item is None:
        raise HTTPException(status_code=404, detail="资产不存在")
    ensure_room_access(db, user, item.room_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    commit_or_400(db)
    db.refresh(item)
    return AssetOut.model_validate(asset_dict(db, item))
