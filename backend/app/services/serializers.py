from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Asset,
    AssetCategory,
    Attachment,
    Building,
    Department,
    ItemRecord,
    Notice,
    RechargeOrder,
    RepairOrder,
    Room,
    RoomAssignment,
    Student,
    User,
    UtilityAccount,
    UtilityBill,
    Visitor,
)
from app.services.common import mask_id_no


def room_dict(db: Session, room: Room, with_occupancy: bool = True) -> dict:
    building = db.get(Building, room.building_id)
    data = {
        "id": room.id,
        "building_id": room.building_id,
        "building_name": building.name if building else None,
        "room_no": room.room_no,
        "floor": room.floor,
        "phone": room.phone,
        "capacity": room.capacity,
        "gender": room.gender,
        "status": room.status,
    }
    if with_occupancy:
        from sqlalchemy import func

        occupied_count = db.scalar(
            select(func.count(RoomAssignment.id)).where(
                RoomAssignment.room_id == room.id,
                RoomAssignment.check_out_at.is_(None),
            )
        ) or 0
        data["occupied_count"] = int(occupied_count)
        data["available_beds"] = max(room.capacity - int(occupied_count), 0)
    return data


def student_dict(db: Session, student: Student) -> dict:
    department = db.get(Department, student.department_id) if student.department_id else None
    assignment = db.scalar(
        select(RoomAssignment)
        .where(
            RoomAssignment.student_id == student.id,
            RoomAssignment.check_out_at.is_(None),
        )
        .limit(1)
    )
    room = db.get(Room, assignment.room_id) if assignment else None
    building = db.get(Building, room.building_id) if room else None
    return {
        "id": student.id,
        "user_id": student.user_id,
        "student_no": student.student_no,
        "name": student.name,
        "gender": student.gender,
        "department_id": student.department_id,
        "department_name": department.name if department else None,
        "class_name": student.class_name,
        "phone": student.phone,
        "is_dorm_leader": bool(student.is_dorm_leader),
        "status": student.status,
        "building_id": building.id if building else None,
        "building_name": building.name if building else None,
        "room_id": room.id if room else None,
        "room_no": room.room_no if room else None,
        "bed_no": assignment.bed_no if assignment else None,
    }


def assignment_dict(db: Session, assignment: RoomAssignment) -> dict:
    student = db.get(Student, assignment.student_id)
    room = db.get(Room, assignment.room_id)
    building = db.get(Building, room.building_id) if room else None
    return {
        "id": assignment.id,
        "student_id": assignment.student_id,
        "student_no": student.student_no if student else None,
        "student_name": student.name if student else None,
        "room_id": assignment.room_id,
        "building_id": building.id if building else None,
        "building_name": building.name if building else None,
        "room_no": room.room_no if room else None,
        "bed_no": assignment.bed_no,
        "check_in_at": assignment.check_in_at,
        "check_out_at": assignment.check_out_at,
        "status": assignment.status,
        "remark": assignment.remark,
    }


def asset_dict(db: Session, asset: Asset) -> dict:
    category = db.get(AssetCategory, asset.category_id)
    room = db.get(Room, asset.room_id)
    building = db.get(Building, room.building_id) if room else None
    return {
        "id": asset.id,
        "asset_no": asset.asset_no,
        "category_id": asset.category_id,
        "category_name": category.name if category else None,
        "room_id": asset.room_id,
        "building_id": building.id if building else None,
        "building_name": building.name if building else None,
        "room_no": room.room_no if room else None,
        "name": asset.name,
        "brand": asset.brand,
        "purchase_date": asset.purchase_date,
        "status": asset.status,
        "remark": asset.remark,
    }


def repair_dict(db: Session, order: RepairOrder) -> dict:
    room = db.get(Room, order.room_id)
    building = db.get(Building, room.building_id) if room else None
    reporter = db.get(User, order.reporter_id)
    handler = db.get(User, order.handler_id) if order.handler_id else None
    return {
        "id": order.id,
        "order_no": order.order_no,
        "room_id": order.room_id,
        "building_id": building.id if building else None,
        "building_name": building.name if building else None,
        "room_no": room.room_no if room else None,
        "asset_id": order.asset_id,
        "asset_name": order.asset_name,
        "reporter_id": order.reporter_id,
        "reporter_name": reporter.real_name if reporter else None,
        "description": order.description,
        "priority": order.priority,
        "status": order.status,
        "handler_id": order.handler_id,
        "handler_name": handler.real_name if handler else None,
        "reported_at": order.reported_at,
        "accepted_at": order.accepted_at,
        "resolved_at": order.resolved_at,
        "solution": order.solution,
        "cancel_reason": order.cancel_reason,
    }


def account_dict(db: Session, account: UtilityAccount) -> dict:
    room = db.get(Room, account.room_id)
    building = db.get(Building, room.building_id) if room else None
    return {
        "id": account.id,
        "room_id": account.room_id,
        "building_id": building.id if building else None,
        "building_name": building.name if building else None,
        "room_no": room.room_no if room else None,
        "balance": account.balance,
        "status": account.status,
    }


def bill_dict(db: Session, bill: UtilityBill) -> dict:
    room = db.get(Room, bill.room_id)
    building = db.get(Building, room.building_id) if room else None
    return {
        "id": bill.id,
        "bill_no": bill.bill_no,
        "room_id": bill.room_id,
        "building_id": building.id if building else None,
        "building_name": building.name if building else None,
        "room_no": room.room_no if room else None,
        "bill_month": bill.bill_month,
        "water_prev": bill.water_prev,
        "water_curr": bill.water_curr,
        "water_unit_price": bill.water_unit_price,
        "water_usage": bill.water_usage,
        "water_amount": bill.water_amount,
        "electricity_prev": bill.electricity_prev,
        "electricity_curr": bill.electricity_curr,
        "electricity_unit_price": bill.electricity_unit_price,
        "electricity_usage": bill.electricity_usage,
        "electricity_amount": bill.electricity_amount,
        "total_amount": bill.total_amount,
        "status": bill.status,
        "due_date": bill.due_date,
        "generated_by": bill.generated_by,
        "generated_at": bill.generated_at,
        "paid_at": bill.paid_at,
        "remark": bill.remark,
    }


def recharge_dict(db: Session, order: RechargeOrder) -> dict:
    account = db.get(UtilityAccount, order.account_id)
    room = db.get(Room, account.room_id) if account else None
    return {
        "id": order.id,
        "order_no": order.order_no,
        "account_id": order.account_id,
        "room_id": room.id if room else None,
        "room_no": room.room_no if room else None,
        "amount": order.amount,
        "pay_method": order.pay_method,
        "status": order.status,
        "created_by": order.created_by,
        "paid_at": order.paid_at,
        "remark": order.remark,
    }


def visitor_dict(db: Session, visitor: Visitor) -> dict:
    host = db.get(Student, visitor.host_student_id)
    room = db.get(Room, visitor.room_id)
    building = db.get(Building, room.building_id) if room else None
    return {
        "id": visitor.id,
        "visitor_name": visitor.visitor_name,
        "id_type": visitor.id_type,
        "id_no_masked": mask_id_no(visitor.id_no),
        "phone": visitor.phone,
        "host_student_id": visitor.host_student_id,
        "host_student_name": host.name if host else None,
        "room_id": visitor.room_id,
        "building_name": building.name if building else None,
        "room_no": room.room_no if room else None,
        "visit_at": visitor.visit_at,
        "leave_at": visitor.leave_at,
        "reason": visitor.reason,
        "status": visitor.status,
        "registered_by": visitor.registered_by,
        "remark": visitor.remark,
    }


def item_dict(db: Session, item: ItemRecord) -> dict:
    student = db.get(Student, item.student_id)
    room = db.get(Room, item.room_id)
    building = db.get(Building, room.building_id) if room else None
    return {
        "id": item.id,
        "room_id": item.room_id,
        "building_name": building.name if building else None,
        "room_no": room.room_no if room else None,
        "student_id": item.student_id,
        "student_name": student.name if student else None,
        "item_name": item.item_name,
        "quantity": item.quantity,
        "unit": item.unit,
        "direction": item.direction,
        "occurred_at": item.occurred_at,
        "reason": item.reason,
        "status": item.status,
        "reviewed_by": item.reviewed_by,
        "reviewed_at": item.reviewed_at,
        "review_remark": item.review_remark,
    }


def notice_dict(db: Session, notice: Notice) -> dict:
    building = db.get(Building, notice.building_id)
    room = db.get(Room, notice.room_id) if notice.room_id else None
    author = db.get(User, notice.author_id)
    return {
        "id": notice.id,
        "building_id": notice.building_id,
        "building_name": building.name if building else None,
        "room_id": notice.room_id,
        "room_no": room.room_no if room else None,
        "author_id": notice.author_id,
        "author_name": author.real_name if author else None,
        "title": notice.title,
        "content": notice.content,
        "scope": notice.scope,
        "status": notice.status,
        "published_at": notice.published_at,
    }


def attachment_dict(attachment: Attachment) -> dict:
    return {
        "id": attachment.id,
        "biz_type": attachment.biz_type,
        "biz_id": attachment.biz_id,
        "file_name": attachment.file_name,
        "file_size": attachment.file_size,
        "mime_type": attachment.mime_type,
        "uploaded_by": attachment.uploaded_by,
        "created_at": attachment.created_at,
        "download_url": f"/api/v1/attachments/{attachment.id}",
    }
