import secrets
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def paginate(db: Session, stmt, page: int, page_size: int) -> tuple[list[Any], int]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return list(items), int(total)


def get_or_404(db: Session, model, obj_id: int, name: str = "记录"):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{name}不存在")
    return obj


def make_no(prefix: str) -> str:
    return f"{prefix}{datetime.now():%Y%m%d%H%M%S}{secrets.randbelow(9000) + 1000}"


def commit_or_400(db: Session, message: str = "数据保存失败，请检查输入") -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=message) from exc


def mask_id_no(value: str | None) -> str | None:
    if not value:
        return value
    if len(value) <= 4:
        return value[:1] + "*" * (len(value) - 1)
    if len(value) <= 8:
        return value[:2] + "*" * (len(value) - 4) + value[-2:]
    return value[:4] + "*" * (len(value) - 8) + value[-4:]
