"""本地端到端冒烟测试。会写入测试数据，执行后可 reset 数据库。"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402


def must(resp, code=200, label=""):
    if resp.status_code != code:
        raise AssertionError(f"{label}: {resp.status_code} {resp.text}")
    return resp.json()


def main() -> int:
    client = TestClient(app)
    admin = must(
        client.post(
            "/api/v1/auth/login",
            json={"username": settings.admin_username, "password": settings.admin_initial_password},
        ),
        200,
        "admin login",
    )
    ah = {"Authorization": f"Bearer {admin['access_token']}"}

    # 员工账号
    manager = must(
        client.post(
            "/api/v1/users",
            headers=ah,
            json={
                "username": "smoke_manager",
                "password": "Smoke@123456",
                "real_name": "冒烟楼管",
                "role": "building_admin",
            },
        ),
        200,
        "create manager",
    )
    must(client.put(f"/api/v1/users/{manager['id']}/buildings", headers=ah, json={"building_ids": [1]}), 200, "bind manager")
    worker = must(
        client.post(
            "/api/v1/users",
            headers=ah,
            json={
                "username": "smoke_worker",
                "password": "Smoke@123456",
                "real_name": "冒烟水电工",
                "role": "worker",
            },
        ),
        200,
        "create worker",
    )
    must(client.put(f"/api/v1/users/{worker['id']}/buildings", headers=ah, json={"building_ids": [1, 2]}), 200, "bind worker")

    # 学生账号与档案
    student_user = must(
        client.post(
            "/api/v1/users",
            headers=ah,
            json={
                "username": "smoke_student",
                "password": "Smoke@123456",
                "real_name": "冒烟学生",
                "role": "student",
            },
        ),
        200,
        "create student user",
    )
    student = must(
        client.post(
            "/api/v1/students",
            headers=ah,
            json={
                "student_no": "SMOKE0001",
                "name": "冒烟学生",
                "gender": "male",
                "department_id": 1,
                "class_name": "软件 2601",
                "user_id": student_user["id"],
                "is_dorm_leader": True,
            },
        ),
        200,
        "create student",
    )
    assignment = must(
        client.post(
            "/api/v1/assignments",
            headers=ah,
            json={"student_id": student["id"], "room_id": 1, "bed_no": "SMOKE-B1"},
        ),
        200,
        "assign room",
    )
    print("assignment", assignment["room_no"], assignment["bed_no"])

    # 学生登录
    stu = must(
        client.post(
            "/api/v1/auth/login",
            json={"username": "smoke_student", "password": "Smoke@123456"},
        ),
        200,
        "student login",
    )
    sh = {"Authorization": f"Bearer {stu['access_token']}"}
    must(client.get("/api/v1/students/me", headers=sh), 200, "student me")
    me_assignment = must(client.get("/api/v1/assignments/me", headers=sh), 200, "assignment me")
    if me_assignment["room_id"] != 1:
        raise AssertionError("assignment me room mismatch")

    # 报修流程
    repair = must(
        client.post(
            "/api/v1/repairs",
            headers=sh,
            json={"asset_id": 1, "description": "冒烟测试：灯泡不亮", "priority": "normal"},
        ),
        200,
        "create repair",
    )
    wrk = must(
        client.post(
            "/api/v1/auth/login",
            json={"username": "smoke_worker", "password": "Smoke@123456"},
        ),
        200,
        "worker login",
    )
    wh = {"Authorization": f"Bearer {wrk['access_token']}"}
    must(client.post(f"/api/v1/repairs/{repair['id']}/accept", headers=wh, json={}), 200, "accept repair")
    done = must(
        client.post(
            f"/api/v1/repairs/{repair['id']}/complete",
            headers=wh,
            json={"solution": "已更换灯泡"},
        ),
        200,
        "complete repair",
    )
    if done["status"] != "completed":
        raise AssertionError("repair not completed")

    # 水电：充值 -> 账单 -> 余额支付
    accounts = must(client.get("/api/v1/utilities/accounts?room_id=1", headers=ah), 200, "accounts")
    account_id = accounts["items"][0]["id"]
    recharge = must(
        client.post(
            "/api/v1/utilities/recharges",
            headers=sh,
            json={"account_id": account_id, "amount": "100.00", "pay_method": "wechat_mock"},
        ),
        200,
        "create recharge",
    )
    must(client.post(f"/api/v1/utilities/recharges/{recharge['id']}/pay", headers=sh), 200, "pay recharge")
    bill = must(
        client.post(
            "/api/v1/utilities/bills",
            headers=wh,
            json={
                "room_id": 1,
                "bill_month": "2026-11-01",
                "water_prev": "100.00",
                "water_curr": "110.00",
                "water_unit_price": "3.5000",
                "electricity_prev": "200.00",
                "electricity_curr": "250.00",
                "electricity_unit_price": "0.6000",
                "due_date": "2026-11-30",
            },
        ),
        200,
        "create bill",
    )
    if str(bill["total_amount"]) != "65.00":
        raise AssertionError(f"bill total mismatch: {bill['total_amount']}")
    paid = must(client.post(f"/api/v1/utilities/bills/{bill['id']}/pay", headers=sh), 200, "pay bill")
    if paid["status"] != "paid":
        raise AssertionError("bill not paid")

    # 访客
    visitor = must(
        client.post(
            "/api/v1/visitors",
            headers=sh,
            json={"visitor_name": "访客甲", "id_no": "110101200001011234", "reason": "送书"},
        ),
        200,
        "create visitor",
    )
    must(client.post(f"/api/v1/visitors/{visitor['id']}/leave", headers=sh), 200, "visitor leave")

    # 物品出入与审核
    item = must(
        client.post(
            "/api/v1/items",
            headers=sh,
            json={"item_name": "电脑", "quantity": 1, "direction": "in", "reason": "返校"},
        ),
        200,
        "create item",
    )
    must(
        client.post(
            f"/api/v1/items/{item['id']}/review",
            headers=ah,
            json={"status": "approved", "remark": "同意"},
        ),
        200,
        "review item",
    )

    # 舍长发布寝室公告
    notice = must(
        client.post(
            "/api/v1/notices",
            headers=sh,
            json={"title": "寝室卫生提醒", "content": "周六上午大扫除", "scope": "room"},
        ),
        200,
        "create notice",
    )
    if notice["scope"] != "room":
        raise AssertionError("notice scope mismatch")
    must(client.get("/api/v1/notices", headers=sh), 200, "list notices")
    unread = must(client.get("/api/v1/notifications/unread-count", headers=sh), 200, "unread")
    print("unread notifications", unread["count"])
    must(client.get("/api/v1/dashboard", headers=sh), 200, "student dashboard")
    must(client.get("/api/v1/dashboard", headers=wh), 200, "worker dashboard")

    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
