from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Notification, User
from app.schemas import Message, NotificationOut, Page
from app.services.common import commit_or_400, paginate

router = APIRouter(prefix="/notifications", tags=["通知"])


@router.get("", response_model=Page[NotificationOut], summary="我的通知")
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[NotificationOut]:
    stmt = select(Notification).where(Notification.user_id == user.id).order_by(Notification.id.desc())
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    rows, total = paginate(db, stmt, page, page_size)
    return Page(
        items=[NotificationOut.model_validate(x) for x in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/unread-count", summary="未读通知数")
def unread_count(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    count = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user.id,
            Notification.is_read.is_(False),
        )
    ) or 0
    return {"count": int(count)}


@router.post("/{notification_id}/read", response_model=Message, summary="标记已读")
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Message:
    item = db.get(Notification, notification_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="通知不存在")
    if not item.is_read:
        item.is_read = True
        item.read_at = datetime.now()
        commit_or_400(db)
    return Message(message="已标记为已读")


@router.post("/read-all", response_model=Message, summary="全部标记已读")
def read_all(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Message:
    db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.is_read.is_(False))
        .values(is_read=True, read_at=datetime.now())
    )
    db.commit()
    return Message(message="全部通知已标记为已读")
