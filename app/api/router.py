from fastapi import APIRouter

# Change your imports to pull the specific router variable instance
from app.modules.auth.router import router as auth
from app.modules.users.router import router as users
from app.modules.dashboard.router import router as dashboard

api = APIRouter()

# Pass the imported variables directly into include_router
api.include_router(auth, prefix="/auth", tags=["auth"])
api.include_router(users, prefix="/users", tags=["users"])
api.include_router(dashboard, prefix="/dashboard", tags=["dashboard"])
