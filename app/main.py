import os
from typing import Annotated
from pathlib import Path
import uvicorn
from fastapi import FastAPI, Request, Response, Form, HTTPException, status, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.database import engine
from app.shared.models import BaseModel
# Import all models to ensure they are registered with BaseModel.metadata
from app.modules.users.model import User
from app.modules.roles.model import Role
from app.modules.permissions.model import Permission 
from app.modules.employee.model import Employee
from app.modules.branch.model import Branch
from app.modules.department.model import OrgUnitType
from app.modules.attendance.model import Attendance
from app.modules.leave.model import LeaveRequest
from app.modules.holiday.model import Holiday
from app.modules.shifts.model import Shift
from app.modules.asset_mgmt.model import Asset, AssetCategory, AssetAssignment, AssetRequest, AssetRepairRequest, AssetMaintenance, AssetHistory, BulkJob

# Create database tables
BaseModel.metadata.create_all(bind=engine)

from app.api.router import api
from app.core.templates import templates
from app.api import deps

app = FastAPI()

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        if "text/html" in request.headers.get("accept", ""):
            return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# 1. Calculate the absolute path to your static asset directory root
APP_ROOT = Path(__file__).resolve().parent
STATIC_DIR = os.path.join(APP_ROOT, "core", "static")

# 2. Mount the directory so files inside it are served at "/static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include Routers
app.include_router(api)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, current_user: Annotated[User, Depends(deps.get_current_user)]):
    # Get theme from cookie, default to 'light'
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request, 
        name="index.html",
        context={"theme": theme, "user": current_user}
    )

@app.post("/set-theme")
async def set_theme(response: Response, theme: str = Form(...)):
    # We create a response that will set the cookie
    content = {"status": "success", "theme": theme}
    resp = JSONResponse(content=content)
    resp.set_cookie(
        key="theme", 
        value=theme, 
        samesite="lax", 
        path="/"
    )
    return resp

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
