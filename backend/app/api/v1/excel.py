from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.assignments import _check_bed_free, _check_student_room
from app.core.deps import building_ids_for_user, get_current_user, require_roles
from app.db.session import get_db
from app.models import (
    Building,
    Department,
    RepairOrder,
    Room,
    RoomAssignment,
    Student,
    User,
    UtilityAccount,
    UtilityBill,
    Visitor,
)
from app.services.common import commit_or_400
from app.services.excel import (
    fmt_datetime,
    make_workbook,
    parse_bool,
    parse_datetime,
    parse_gender,
    read_sheet,
    workbook_response,
)
from app.services.serializers import (
    assignment_dict,
    bill_dict,
    repair_dict,
    student_dict,
    visitor_dict,
)

router = APIRouter(prefix="/excel", tags=["Excel 导入导出"])

staff_only = require_roles("sys_admin", "building_admin", "worker")
writer_only = require_roles("sys_admin", "building_admin")

GENDER_CN = {"male": "男", "female": "女", "other": "其他"}
ASSIGNMENT_STATUS_CN = {"active": "在住", "transferring": "调宿中", "checked_out": "已退宿"}
REPAIR_STATUS_CN = {
    "pending": "待受理",
    "processing": "维修中",
    "completed": "已办结",
    "cancelled": "已取消",
}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _scoped_room_ids(db: Session, user: User):
    allowed = building_ids_for_user(db, user)
    if allowed is None:
        return None
    if not allowed:
        return select(Room.id).where(Room.id == -1)
    return select(Room.id).where(Room.building_id.in_(allowed))


@router.get("/templates/students", summary="下载学生导入模板")
def student_template(_: User = Depends(writer_only)):
    headers = ["学号", "姓名", "性别", "院系编码", "班级", "手机号", "是否舍长"]
    wb = make_workbook(
        "学生导入模板",
        headers,
        [
            ["20260001", "张三", "男", "CS", "软件 2601", "13800000000", "否"],
            ["20260002", "李四", "女", "SE", "软件 2602", "13900000000", "是"],
        ],
        widths=[16, 12, 8, 12, 16, 16, 12],
    )
    return workbook_response(wb, "students_template.xlsx")


@router.get("/templates/assignments", summary="下载宿舍分配导入模板")
def assignment_template(_: User = Depends(writer_only)):
    headers = ["学号", "楼栋编码", "房间号", "床位号", "入住时间"]
    wb = make_workbook(
        "宿舍分配导入模板",
        headers,
        [["20260001", "B01", "101", "1", "2026-09-01 08:00:00"]],
        widths=[16, 12, 12, 12, 22],
    )
    return workbook_response(wb, "assignments_template.xlsx")


@router.post("/import/students", summary="Excel 导入学生")
async def import_students(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(writer_only),
) -> dict:
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Excel 文件不能超过 10MB")
    try:
        rows, _headers = read_sheet(
            content,
            ["学号", "姓名", "性别", "院系编码", "班级", "手机号", "是否舍长"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not rows:
        raise HTTPException(status_code=400, detail="Excel 没有数据行")

    departments = db.scalars(select(Department)).all()
    dept_by_code = {d.code.upper(): d for d in departments}
    dept_by_name = {d.name: d for d in departments}
    existing = set(db.scalars(select(Student.student_no)).all())
    seen: set[str] = set()
    errors: list[str] = []
    items: list[Student] = []

    for row in rows:
        row_no = row["_row"]
        student_no = _text(row["学号"])
        name = _text(row["姓名"])
        dept_key = _text(row["院系编码"])
        if not student_no:
            errors.append(f"第{row_no}行：学号为空")
            continue
        if student_no in existing or student_no in seen:
            errors.append(f"第{row_no}行：学号 {student_no} 已存在")
            continue
        if not name:
            errors.append(f"第{row_no}行：姓名为空")
            continue
        dept = dept_by_code.get(dept_key.upper()) or dept_by_name.get(dept_key)
        if dept is None:
            errors.append(f"第{row_no}行：院系 {dept_key} 不存在")
            continue
        seen.add(student_no)
        items.append(
            Student(
                student_no=student_no,
                name=name,
                gender=parse_gender(row["性别"]),
                department_id=dept.id,
                class_name=_text(row["班级"]) or None,
                phone=_text(row["手机号"]) or None,
                is_dorm_leader=parse_bool(row["是否舍长"]),
                status="active",
            )
        )

    if errors:
        raise HTTPException(status_code=400, detail={"message": "导入校验失败", "errors": errors})

    db.add_all(items)
    commit_or_400(db, "学生导入失败")
    return {"total": len(rows), "success": len(items), "failed": 0}


@router.post("/import/assignments", summary="Excel 导入宿舍分配")
async def import_assignments(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(writer_only),
) -> dict:
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Excel 文件不能超过 10MB")
    try:
        rows, _headers = read_sheet(
            content,
            ["学号", "楼栋编码", "房间号", "床位号", "入住时间"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not rows:
        raise HTTPException(status_code=400, detail="Excel 没有数据行")

    allowed = building_ids_for_user(db, user)
    buildings = {b.code.upper(): b for b in db.scalars(select(Building)).all()}
    students = {s.student_no: s for s in db.scalars(select(Student)).all()}
    active_student_ids = set(
        db.scalars(
            select(RoomAssignment.student_id).where(RoomAssignment.check_out_at.is_(None))
        ).all()
    )
    seen_students: set[int] = set()
    seen_beds: set[tuple[int, str]] = set()
    room_extra_count: dict[int, int] = {}
    errors: list[str] = []
    items: list[RoomAssignment] = []

    for row in rows:
        row_no = row["_row"]
        student_no = _text(row["学号"])
        building_code = _text(row["楼栋编码"]).upper()
        room_no = _text(row["房间号"])
        bed_no = _text(row["床位号"])
        student = students.get(student_no)
        building = buildings.get(building_code)
        if student is None:
            errors.append(f"第{row_no}行：学号 {student_no} 不存在")
            continue
        if student.id in active_student_ids or student.id in seen_students:
            errors.append(f"第{row_no}行：学生 {student_no} 已有当前住宿")
            continue
        if building is None:
            errors.append(f"第{row_no}行：楼栋 {building_code} 不存在")
            continue
        if allowed is not None and building.id not in allowed:
            errors.append(f"第{row_no}行：无权分配楼栋 {building_code}")
            continue
        room = db.scalar(
            select(Room).where(Room.building_id == building.id, Room.room_no == room_no)
        )
        if room is None:
            errors.append(f"第{row_no}行：房间 {building_code}-{room_no} 不存在")
            continue
        if not bed_no:
            errors.append(f"第{row_no}行：床位号为空")
            continue
        try:
            _check_student_room(db, student, room)
            _check_bed_free(db, room.id, bed_no)
        except HTTPException as exc:
            errors.append(f"第{row_no}行：{exc.detail}")
            continue
        key = (room.id, bed_no)
        if key in seen_beds:
            errors.append(f"第{row_no}行：床位 {building_code}-{room_no}-{bed_no} 重复")
            continue
        extra = room_extra_count.get(room.id, 0)
        # 用数量而不是单条记录判断容量
        from sqlalchemy import func

        occupied_count = db.scalar(
            select(func.count(RoomAssignment.id)).where(
                RoomAssignment.room_id == room.id,
                RoomAssignment.check_out_at.is_(None),
            )
        ) or 0
        if occupied_count + extra >= room.capacity:
            errors.append(f"第{row_no}行：房间 {building_code}-{room_no} 已满")
            continue
        try:
            check_in_at = parse_datetime(row["入住时间"]) or datetime.now()
        except ValueError as exc:
            errors.append(f"第{row_no}行：{exc}")
            continue

        seen_students.add(student.id)
        seen_beds.add(key)
        room_extra_count[room.id] = extra + 1
        items.append(
            RoomAssignment(
                student_id=student.id,
                room_id=room.id,
                bed_no=bed_no,
                check_in_at=check_in_at,
                status="active",
                remark="Excel 导入",
            )
        )

    if errors:
        raise HTTPException(status_code=400, detail={"message": "导入校验失败", "errors": errors})

    db.add_all(items)
    commit_or_400(db, "宿舍分配导入失败")
    return {"total": len(rows), "success": len(items), "failed": 0}


@router.get("/export/students", summary="导出学生名单")
def export_students(
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
):
    stmt = select(Student).order_by(Student.student_no)
    scoped_rooms = _scoped_room_ids(db, user)
    if scoped_rooms is not None:
        student_ids = select(RoomAssignment.student_id).where(
            RoomAssignment.room_id.in_(scoped_rooms),
            RoomAssignment.check_out_at.is_(None),
        )
        stmt = stmt.where(Student.id.in_(student_ids))
    rows = []
    for student in db.scalars(stmt).all():
        data = student_dict(db, student)
        rows.append([
            data["student_no"],
            data["name"],
            GENDER_CN.get(data["gender"], data["gender"]),
            data["department_name"] or "",
            data["class_name"] or "",
            data["phone"] or "",
            "是" if data["is_dorm_leader"] else "否",
            data["status"],
            data["building_name"] or "",
            data["room_no"] or "",
            data["bed_no"] or "",
        ])
    wb = make_workbook(
        "学生名单",
        ["学号", "姓名", "性别", "院系", "班级", "手机号", "舍长", "学籍状态", "楼栋", "房间", "床位"],
        rows,
        widths=[16, 12, 8, 24, 16, 16, 8, 10, 12, 10, 10],
    )
    return workbook_response(wb, f"students_{datetime.now():%Y%m%d}.xlsx")


@router.get("/export/assignments", summary="导出住宿记录")
def export_assignments(
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
):
    stmt = select(RoomAssignment).order_by(RoomAssignment.id.desc())
    scoped_rooms = _scoped_room_ids(db, user)
    if scoped_rooms is not None:
        stmt = stmt.where(RoomAssignment.room_id.in_(scoped_rooms))
    rows = []
    for item in db.scalars(stmt).all():
        data = assignment_dict(db, item)
        rows.append([
            data["student_no"] or "",
            data["student_name"] or "",
            data["building_name"] or "",
            data["room_no"] or "",
            data["bed_no"],
            fmt_datetime(data["check_in_at"]),
            fmt_datetime(data["check_out_at"]),
            ASSIGNMENT_STATUS_CN.get(data["status"], data["status"]),
        ])
    wb = make_workbook(
        "住宿记录",
        ["学号", "姓名", "楼栋", "房间", "床位", "入住时间", "退宿时间", "状态"],
        rows,
        widths=[16, 12, 12, 10, 10, 22, 22, 12],
    )
    return workbook_response(wb, f"assignments_{datetime.now():%Y%m%d}.xlsx")


@router.get("/export/repairs", summary="导出报修记录")
def export_repairs(
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
):
    stmt = select(RepairOrder).order_by(RepairOrder.id.desc())
    scoped_rooms = _scoped_room_ids(db, user)
    if scoped_rooms is not None:
        stmt = stmt.where(RepairOrder.room_id.in_(scoped_rooms))
    rows = []
    for order in db.scalars(stmt).all():
        data = repair_dict(db, order)
        rows.append([
            data["order_no"],
            data["building_name"] or "",
            data["room_no"] or "",
            data["asset_name"] or "",
            data["reporter_name"] or "",
            data["description"],
            data["priority"],
            REPAIR_STATUS_CN.get(data["status"], data["status"]),
            fmt_datetime(data["reported_at"]),
            fmt_datetime(data["resolved_at"]),
            data["handler_name"] or "",
            data["solution"] or "",
        ])
    wb = make_workbook(
        "报修记录",
        ["报修单号", "楼栋", "房间", "资产", "报修人", "故障描述", "优先级", "状态", "报修时间", "解决时间", "处理人", "处理方案"],
        rows,
        widths=[20, 12, 10, 16, 12, 30, 10, 10, 22, 22, 12, 30],
    )
    return workbook_response(wb, f"repairs_{datetime.now():%Y%m%d}.xlsx")


@router.get("/export/utility-bills", summary="导出水电账单")
def export_bills(
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
):
    stmt = select(UtilityBill).order_by(UtilityBill.bill_month.desc(), UtilityBill.id.desc())
    scoped_rooms = _scoped_room_ids(db, user)
    if scoped_rooms is not None:
        stmt = stmt.where(UtilityBill.room_id.in_(scoped_rooms))
    rows = []
    for bill in db.scalars(stmt).all():
        data = bill_dict(db, bill)
        rows.append([
            data["bill_no"],
            data["building_name"] or "",
            data["room_no"] or "",
            data["bill_month"].strftime("%Y-%m") if data["bill_month"] else "",
            str(data["water_usage"] or 0),
            str(data["water_amount"] or 0),
            str(data["electricity_usage"] or 0),
            str(data["electricity_amount"] or 0),
            str(data["total_amount"] or 0),
            data["status"],
            fmt_datetime(data["paid_at"]),
        ])
    wb = make_workbook(
        "水电账单",
        ["账单号", "楼栋", "房间", "月份", "用水量", "水费", "用电量", "电费", "合计", "状态", "缴费时间"],
        rows,
        widths=[20, 12, 10, 10, 10, 10, 10, 10, 12, 10, 22],
    )
    return workbook_response(wb, f"utility_bills_{datetime.now():%Y%m%d}.xlsx")


@router.get("/export/visitors", summary="导出访客记录")
def export_visitors(
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
):
    stmt = select(Visitor).order_by(Visitor.id.desc())
    scoped_rooms = _scoped_room_ids(db, user)
    if scoped_rooms is not None:
        stmt = stmt.where(Visitor.room_id.in_(scoped_rooms))
    rows = []
    for visitor in db.scalars(stmt).all():
        data = visitor_dict(db, visitor)
        rows.append([
            data["visitor_name"],
            data["id_no_masked"] or "",
            data["phone"] or "",
            data["host_student_name"] or "",
            data["building_name"] or "",
            data["room_no"] or "",
            fmt_datetime(data["visit_at"]),
            fmt_datetime(data["leave_at"]),
            data["status"],
            data["reason"] or "",
        ])
    wb = make_workbook(
        "访客记录",
        ["访客姓名", "证件号（脱敏）", "电话", "被访学生", "楼栋", "房间", "来访时间", "离开时间", "状态", "事由"],
        rows,
        widths=[12, 20, 16, 12, 12, 10, 22, 22, 10, 24],
    )
    return workbook_response(wb, f"visitors_{datetime.now():%Y%m%d}.xlsx")
