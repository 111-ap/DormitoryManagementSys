from sqlalchemy.orm import Session

from app.models import Notification


def notify(
    db: Session,
    user_id: int,
    type_: str,
    title: str,
    content: str | None = None,
    related_type: str | None = None,
    related_id: int | None = None,
) -> Notification:
    item = Notification(
        user_id=user_id,
        type=type_,
        title=title,
        content=content,
        related_type=related_type,
        related_id=related_id,
    )
    db.add(item)
    return item


def notify_many(
    db: Session,
    user_ids: list[int],
    type_: str,
    title: str,
    content: str | None = None,
    related_type: str | None = None,
    related_id: int | None = None,
) -> None:
    for user_id in set(user_ids):
        notify(db, user_id, type_, title, content, related_type, related_id)
