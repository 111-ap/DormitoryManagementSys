from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import PROJECT_DIR, settings
from app.core.deps import building_ids_for_user, get_current_user
from app.db.session import get_db
from app.models import Attachment, ItemRecord, Notice, RepairOrder, Room, Student, User, Visitor
from app.schemas import AttachmentOut, Message
from app.services.common import commit_or_400
from app.services.serializers import attachment_dict

router = APIRouter(prefix="/attachments", tags=["附件"])

ALLOWED_BIZ_TYPES = {"repair", "visitor", "item", "notice"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _upload_root() -> Path:
    root = Path(settings.upload_dir)
    if not root.is_absolute():
        root = PROJECT_DIR / root
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _room_building_id(db: Session, room_id: int) -> int:
    room = db.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="房间不存在")
    return room.building_id


def _ensure_business_access(
    db: Session,
    user: User,
    biz_type: str,
    biz_id: int,
    *,
    for_download: bool = False,
) -> None:
    if biz_type not in ALLOWED_BIZ_TYPES:
        raise HTTPException(status_code=400, detail="不支持的附件业务类型")
    allowed = building_ids_for_user(db, user)

    if biz_type == "repair":
        order = db.get(RepairOrder, biz_id)
        if order is None:
            raise HTTPException(status_code=404, detail="报修单不存在")
        if user.role == "student" and order.reporter_id != user.id:
            raise HTTPException(status_code=403, detail="无权访问该报修单附件")
        if user.role != "student" and allowed is not None:
            if _room_building_id(db, order.room_id) not in allowed:
                raise HTTPException(status_code=403, detail="无权访问该报修单附件")
        return

    if biz_type == "visitor":
        visitor = db.get(Visitor, biz_id)
        if visitor is None:
            raise HTTPException(status_code=404, detail="访客记录不存在")
        if user.role == "student":
            student = db.scalar(select(Student).where(Student.user_id == user.id))
            if student is None or visitor.host_student_id != student.id:
                raise HTTPException(status_code=403, detail="无权访问该访客记录")
            if for_download:
                raise HTTPException(status_code=403, detail="访客证件照仅宿舍管理人员可查看")
        elif allowed is not None:
            if _room_building_id(db, visitor.room_id) not in allowed:
                raise HTTPException(status_code=403, detail="无权访问该访客记录")
        return

    if biz_type == "item":
        item = db.get(ItemRecord, biz_id)
        if item is None:
            raise HTTPException(status_code=404, detail="物品记录不存在")
        if user.role == "student":
            student = db.scalar(select(Student).where(Student.user_id == user.id))
            if student is None or item.student_id != student.id:
                raise HTTPException(status_code=403, detail="无权访问该物品记录")
        elif allowed is not None:
            if _room_building_id(db, item.room_id) not in allowed:
                raise HTTPException(status_code=403, detail="无权访问该物品记录")
        return

    if biz_type == "notice":
        notice = db.get(Notice, biz_id)
        if notice is None:
            raise HTTPException(status_code=404, detail="公告不存在")
        if user.role == "student" and notice.author_id != user.id:
            raise HTTPException(status_code=403, detail="无权访问该公告附件")
        if user.role != "student" and allowed is not None:
            if notice.building_id not in allowed:
                raise HTTPException(status_code=403, detail="无权访问该公告附件")


@router.get("", response_model=list[AttachmentOut], summary="业务附件列表")
def list_attachments(
    biz_type: str,
    biz_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AttachmentOut]:
    _ensure_business_access(db, user, biz_type, biz_id)
    rows = db.scalars(
        select(Attachment)
        .where(Attachment.biz_type == biz_type, Attachment.biz_id == biz_id)
        .order_by(Attachment.id)
    ).all()
    return [AttachmentOut.model_validate(attachment_dict(x)) for x in rows]


@router.post("/upload", response_model=AttachmentOut, summary="上传业务附件")
async def upload_attachment(
    biz_type: str = Form(...),
    biz_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AttachmentOut:
    if biz_type not in ALLOWED_BIZ_TYPES:
        raise HTTPException(status_code=400, detail="不支持的附件业务类型")
    _ensure_business_access(db, user, biz_type, biz_id)

    original_name = Path(file.filename or "upload").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="只支持 jpg/jpeg/png/webp 图片")
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="上传文件必须是图片")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"文件不能超过 {settings.max_upload_mb}MB")
    if not content:
        raise HTTPException(status_code=400, detail="上传文件为空")

    now = datetime.now()
    target_dir = _upload_root() / biz_type / f"{now:%Y}" / f"{now:%m}"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{uuid4().hex}{suffix}"
    target.write_bytes(content)
    try:
        relative = target.relative_to(PROJECT_DIR.resolve()).as_posix()
    except ValueError:
        relative = target.as_posix()

    attachment = Attachment(
        biz_type=biz_type,
        biz_id=biz_id,
        file_name=original_name[:255],
        file_path=relative,
        file_size=len(content),
        mime_type=file.content_type or f"image/{suffix.lstrip('.')}",
        uploaded_by=user.id,
    )
    db.add(attachment)
    commit_or_400(db, "附件保存失败")
    db.refresh(attachment)
    return AttachmentOut.model_validate(attachment_dict(attachment))


@router.get("/{attachment_id}", summary="下载业务附件")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    attachment = db.get(Attachment, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="附件不存在")
    _ensure_business_access(db, user, attachment.biz_type, attachment.biz_id, for_download=True)

    path = Path(attachment.file_path)
    if not path.is_absolute():
        path = PROJECT_DIR / path
    path = path.resolve()
    root = _upload_root()
    try:
        path.relative_to(root)
    except ValueError:
        raise HTTPException(status_code=403, detail="非法的附件路径")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="附件文件不存在")
    return FileResponse(path, media_type=attachment.mime_type, filename=attachment.file_name)


@router.delete("/{attachment_id}", response_model=Message, summary="删除附件")
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Message:
    attachment = db.get(Attachment, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="附件不存在")
    _ensure_business_access(db, user, attachment.biz_type, attachment.biz_id)
    if user.role == "student" and attachment.uploaded_by != user.id:
        raise HTTPException(status_code=403, detail="只能删除自己上传的附件")

    path = Path(attachment.file_path)
    if not path.is_absolute():
        path = PROJECT_DIR / path
    path = path.resolve()
    try:
        path.relative_to(_upload_root())
    except ValueError:
        path = None
    db.delete(attachment)
    commit_or_400(db)
    if path and path.is_file():
        path.unlink(missing_ok=True)
    return Message(message="附件已删除")
