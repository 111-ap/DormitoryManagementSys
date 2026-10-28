from fastapi import APIRouter

from app.api.v1 import (
    assets,
    assignments,
    attachments,
    auth,
    buildings,
    dashboard,
    departments,
    excel,
    items,
    notices,
    notifications,
    repairs,
    rooms,
    students,
    users,
    utilities,
    visitors,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(departments.router)
api_router.include_router(buildings.router)
api_router.include_router(rooms.router)
api_router.include_router(students.router)
api_router.include_router(assignments.router)
api_router.include_router(assets.router)
api_router.include_router(repairs.router)
api_router.include_router(attachments.router)
api_router.include_router(excel.router)
api_router.include_router(utilities.router)
api_router.include_router(visitors.router)
api_router.include_router(items.router)
api_router.include_router(notices.router)
api_router.include_router(notifications.router)
api_router.include_router(dashboard.router)
