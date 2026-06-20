from typing import Annotated, Optional
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import date

from app.core.templates import templates
from app.core.database import get_db
from app.modules.leave import service, schema, model
from app.api import deps
from app.modules.users.model import User

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def list_leave_requests(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    leave_requests = service.get_leave_requests(db)
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="leave/templates/leaves.html",
        context={"leave_requests": leave_requests, "theme": theme, "user": current_user}
    )

@router.get("/create", response_class=HTMLResponse)
async def create_leave_request_page(
    request: Request,
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="leave/templates/create-leave.html",
        context={
            "theme": theme, 
            "user": current_user,
            "leave_types": model.LeaveType
        }
    )

@router.post("/create")
async def create_leave_request(
    employee_id: Annotated[int, Form(...)],
    start_date: Annotated[date, Form(...)],
    end_date: Annotated[date, Form(...)],
    leave_type: Annotated[model.LeaveType, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    reason: Annotated[Optional[str], Form()] = None
):
    leave_in = schema.LeaveRequestCreate(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        leave_type=leave_type,
        reason=reason
    )
    service.create_leave_request(db, leave_in)
    return RedirectResponse(url="/leave/", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{leave_id}/edit", response_class=HTMLResponse)
async def edit_leave_request_page(
    leave_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    leave_request = service.get_leave_request(db, leave_id)
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="leave/templates/edit-leave.html",
        context={
            "leave_request": leave_request, 
            "theme": theme, 
            "user": current_user,
            "leave_types": model.LeaveType,
            "leave_statuses": model.LeaveStatus
        }
    )

@router.post("/{leave_id}/edit")
async def edit_leave_request(
    leave_id: int,
    employee_id: Annotated[int, Form(...)],
    start_date: Annotated[date, Form(...)],
    end_date: Annotated[date, Form(...)],
    leave_type: Annotated[model.LeaveType, Form(...)],
    status: Annotated[model.LeaveStatus, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    reason: Annotated[Optional[str], Form()] = None
):
    leave_update = schema.LeaveRequestUpdate(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        leave_type=leave_type,
        status=status,
        reason=reason
    )
    service.update_leave_request(db, leave_id, leave_update)
    return RedirectResponse(url="/leave/", status_code=303)

@router.post("/{leave_id}/approve")
async def approve_leave_request(
    leave_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    leave_update = schema.LeaveRequestUpdate(status=model.LeaveStatus.APPROVED)
    service.update_leave_request(db, leave_id, leave_update)
    return RedirectResponse(url="/leave/", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/{leave_id}/reject")
async def reject_leave_request(
    leave_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    leave_update = schema.LeaveRequestUpdate(status=model.LeaveStatus.REJECTED)
    service.update_leave_request(db, leave_id, leave_update)
    return RedirectResponse(url="/leave/", status_code=status.HTTP_303_SEE_OTHER)
