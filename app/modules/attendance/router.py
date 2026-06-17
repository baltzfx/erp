from typing import Optional, Annotated
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import datetime

from app.core.templates import templates
from app.core.database import get_db
from app.modules.attendance import service, schema
from app.api import deps
from app.modules.users.model import User
from app.modules.employee import service as emp_service

router = APIRouter()

@router.get("/clock-status", response_class=HTMLResponse)
async def clock_status(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    if not current_user.employee:
        return HTMLResponse(content="<p class='text-xs text-red-500'>No employee profile linked</p>")
    
    attendance = service.get_today_attendance(db, current_user.employee.id)
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="attendance/templates/components/clock_button.html",
        context={"attendance": attendance, "theme": theme}
    )

@router.post("/clock-in-out")
async def clock_in_out(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    if not current_user.employee:
        raise HTTPException(status_code=400, detail="User not linked to an employee profile")
    
    employee_id = current_user.employee.id
    attendance = service.get_today_attendance(db, employee_id)
    now = datetime.datetime.now()
    
    if not attendance:
        # Clock In
        attendance_in = schema.AttendanceCreate(
            employee_id=employee_id,
            date=datetime.date.today(),
            check_in=now,
            status=schema.AttendanceStatus.PRESENT
        )
        attendance = service.create_attendance(db, attendance_in)
    elif not attendance.check_out:
        # Clock Out
        attendance_up = schema.AttendanceUpdate(check_out=now)
        attendance = service.update_attendance(db, attendance.id, attendance_up)
    
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="attendance/templates/components/clock_button.html",
        context={"attendance": attendance, "theme": theme}
    )

@router.get("/", response_class=HTMLResponse)
async def list_attendance(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    attendances = service.get_attendances(db)
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="attendance/templates/attendance.html",
        context={"attendances": attendances, "theme": theme, "user": current_user}
    )

@router.get("/create", response_class=HTMLResponse)
async def create_attendance_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    employees = emp_service.get_employees(db)
    theme = request.cookies.get("theme", "light")
    today = datetime.date.today()
    return templates.TemplateResponse(
        request=request,
        name="attendance/templates/create-attendance.html",
        context={
            "theme": theme, 
            "user": current_user, 
            "employees": employees,
            "statuses": schema.AttendanceStatus,
            "today": today
        }
    )

@router.post("/create")
async def create_attendance(
    employee_id: Annotated[int, Form(...)],
    attendance_date: Annotated[datetime.date, Form(alias="date")],
    status_val: Annotated[schema.AttendanceStatus, Form(alias="status")],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    check_in: Annotated[Optional[datetime.datetime], Form()] = None,
    check_out: Annotated[Optional[datetime.datetime], Form()] = None,
    remarks: Annotated[Optional[str], Form()] = None
):
    attendance_in = schema.AttendanceCreate(
        employee_id=employee_id,
        date=attendance_date,
        check_in=check_in,
        check_out=check_out,
        status=status_val,
        remarks=remarks
    )
    service.create_attendance(db, attendance_in)
    return RedirectResponse(url="/attendance/", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{attendance_id}/edit", response_class=HTMLResponse)
async def edit_attendance_page(
    attendance_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    attendance = service.get_attendance(db, attendance_id)
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    employees = emp_service.get_employees(db)
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="attendance/templates/edit-attendance.html",
        context={
            "attendance": attendance, 
            "theme": theme, 
            "user": current_user, 
            "employees": employees,
            "statuses": schema.AttendanceStatus
        }
    )

@router.post("/{attendance_id}/edit")
async def edit_attendance(
    attendance_id: int,
    employee_id: Annotated[int, Form(...)],
    attendance_date: Annotated[datetime.date, Form(alias="date")],
    status_val: Annotated[schema.AttendanceStatus, Form(alias="status")],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    check_in: Annotated[Optional[datetime.datetime], Form()] = None,
    check_out: Annotated[Optional[datetime.datetime], Form()] = None,
    remarks: Annotated[Optional[str], Form()] = None
):
    attendance_in = schema.AttendanceUpdate(
        employee_id=employee_id,
        date=attendance_date,
        check_in=check_in,
        check_out=check_out,
        status=status_val,
        remarks=remarks
    )
    service.update_attendance(db, attendance_id, attendance_in)
    return RedirectResponse(url="/attendance/", status_code=status.HTTP_303_SEE_OTHER)

@router.delete("/{attendance_id}")
async def delete_attendance(
    attendance_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    service.delete_attendance(db, attendance_id)
    return HTMLResponse(content="", status_code=status.HTTP_200_OK)
