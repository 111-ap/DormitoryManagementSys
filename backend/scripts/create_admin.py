"""创建或重置系统管理员账号。

用法（在 backend 目录）：
    .venv\\Scripts\\python.exe scripts\\create_admin.py
    .venv\\Scripts\\python.exe scripts\\create_admin.py --username admin --real-name 系统管理员

密码优先取环境变量 ADMIN_INITIAL_PASSWORD，其次取命令行 --password。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="创建系统管理员")
    parser.add_argument("--username", default=settings.admin_username)
    parser.add_argument("--password", default=settings.admin_initial_password)
    parser.add_argument("--real-name", default="系统管理员")
    args = parser.parse_args()

    if not args.password or args.password == "change_me_admin_password":
        print("错误：请在 .env 设置 ADMIN_INITIAL_PASSWORD，或使用 --password 传入密码")
        return 1

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == args.username))
        if user is None:
            user = User(
                username=args.username,
                password_hash=hash_password(args.password),
                real_name=args.real_name,
                role="sys_admin",
                status="active",
            )
            db.add(user)
            action = "created"
        else:
            user.password_hash = hash_password(args.password)
            user.real_name = args.real_name
            user.role = "sys_admin"
            user.status = "active"
            action = "updated"
        db.commit()
        print(f"admin {action}: {args.username}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
