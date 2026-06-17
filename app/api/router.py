from fastapi import APIRouter

# Change your imports to pull the specific router variable instance
from app.modules.auth.router import router as auth
from app.modules.users.router import router as users
from app.modules.dashboard.router import router as dashboard
from app.modules.roles.router import router as roles
from app.modules.permissions.router import router as permissions
from app.modules.branch.router import router as branch
from app.modules.department.router import router as department
from app.modules.employee.router import router as employee
from app.modules.attendance.router import router as attendance
from app.modules.shifts.router import router as shifts

api = APIRouter()

# Pass the imported variables directly into include_router
api.include_router(auth, prefix="/auth", tags=["auth"])
api.include_router(users, prefix="/users", tags=["users"])
api.include_router(dashboard, prefix="/dashboard", tags=["dashboard"])
api.include_router(roles, prefix="/roles", tags=["roles"])
api.include_router(permissions, prefix="/permissions", tags=["permissions"])
api.include_router(branch, prefix="/branch", tags=["branch"])
api.include_router(department, prefix="/department", tags=["department"])
api.include_router(employee, prefix="/employees", tags=["employees"])
api.include_router(attendance, prefix="/attendance", tags=["attendance"])
api.include_router(shifts, prefix="/shifts", tags=["shifts"])
