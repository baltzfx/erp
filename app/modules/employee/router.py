from typing import Optional, Annotated, List
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.templates import templates
from app.core.database import get_db
from app.modules.employee import service, schema
from app.api import deps
from app.modules.users.model import User
from app.modules.department import service as dept_service
from app.modules.branch import service as branch_service
from app.modules.users import crud as user_service

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def list_employees(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    employees = service.get_employees(db)
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="employee/templates/employee.html",
        context={"employees": employees, "theme": theme, "user": current_user}
    )

@router.get("/create", response_class=HTMLResponse)
async def create_employee_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    departments = dept_service.get_departments(db)
    branches = branch_service.get_branches(db)
    users = user_service.get_users(db)
    supervisors = service.get_employees(db)
    
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="employee/templates/create-employee.html",
        context={
            "theme": theme, 
            "user": current_user,
            "departments": departments,
            "branches": branches,
            "users": users,
            "supervisors": supervisors,
            "genders": schema.GenderEnum,
            "civil_statuses": schema.CivilStatusEnum,
            "emp_statuses": schema.EmpStatusEnum
        }
    )

@router.post("/create")
async def create_employee(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    first_name: Annotated[str, Form(...)],
    last_name: Annotated[str, Form(...)],
    email: Annotated[str, Form(...)],
    middle_name: Annotated[Optional[str], Form()] = None,
    suffix: Annotated[Optional[str], Form()] = None,
    gender: Annotated[Optional[schema.GenderEnum], Form()] = None,
    civil_status: Annotated[Optional[schema.CivilStatusEnum], Form()] = None,
    emp_status: Annotated[Optional[schema.EmpStatusEnum], Form()] = None,
    department_id: Annotated[Optional[str], Form()] = None,
    branch_id: Annotated[Optional[str], Form()] = None,
    user_id: Annotated[Optional[str], Form()] = None,
    supervisor_id: Annotated[Optional[str], Form()] = None,
    position: Annotated[Optional[str], Form()] = None,
    emp_no: Annotated[Optional[str], Form()] = None
):
    # Convert empty strings to None and strings to int for ID fields
    dept_id = int(department_id) if department_id and department_id.strip() else None
    br_id = int(branch_id) if branch_id and branch_id.strip() else None
    u_id = int(user_id) if user_id and user_id.strip() else None
    sup_id = int(supervisor_id) if supervisor_id and supervisor_id.strip() else None

    employee_in = schema.EmployeeCreate(
        first_name=first_name,
        last_name=last_name,
        email=email,
        middle_name=middle_name,
        suffix=suffix,
        gender=gender,
        civil_status=civil_status,
        emp_status=emp_status,
        department_id=dept_id,
        branch_id=br_id,
        user_id=u_id,
        supervisor_id=sup_id,
        position=position,
        emp_no=emp_no
    )
    service.create_employee(db, employee_in)
    return RedirectResponse(url="/employees/", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{employee_id}/edit", response_class=HTMLResponse)
async def edit_employee_page(
    employee_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    employee = service.get_employee(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    departments = dept_service.get_departments(db)
    branches = branch_service.get_branches(db)
    users = user_service.get_users(db)
    supervisors = service.get_employees(db)
    
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="employee/templates/edit-employee.html",
        context={
            "employee": employee, 
            "theme": theme, 
            "user": current_user,
            "departments": departments,
            "branches": branches,
            "users": users,
            "supervisors": supervisors,
            "genders": schema.GenderEnum,
            "civil_statuses": schema.CivilStatusEnum,
            "emp_statuses": schema.EmpStatusEnum
        }
    )

@router.post("/{employee_id}/edit")
async def edit_employee(
    employee_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    first_name: Annotated[str, Form(...)],
    last_name: Annotated[str, Form(...)],
    email: Annotated[str, Form(...)],
    middle_name: Annotated[Optional[str], Form()] = None,
    suffix: Annotated[Optional[str], Form()] = None,
    gender: Annotated[Optional[schema.GenderEnum], Form()] = None,
    civil_status: Annotated[Optional[schema.CivilStatusEnum], Form()] = None,
    emp_status: Annotated[Optional[schema.EmpStatusEnum], Form()] = None,
    department_id: Annotated[Optional[str], Form()] = None,
    branch_id: Annotated[Optional[str], Form()] = None,
    user_id: Annotated[Optional[str], Form()] = None,
    supervisor_id: Annotated[Optional[str], Form()] = None,
    position: Annotated[Optional[str], Form()] = None,
    emp_no: Annotated[Optional[str], Form()] = None
):
    # Convert empty strings to None and strings to int for ID fields
    dept_id = int(department_id) if department_id and department_id.strip() else None
    br_id = int(branch_id) if branch_id and branch_id.strip() else None
    u_id = int(user_id) if user_id and user_id.strip() else None
    sup_id = int(supervisor_id) if supervisor_id and supervisor_id.strip() else None

    employee_in = schema.EmployeeUpdate(
        first_name=first_name,
        last_name=last_name,
        email=email,
        middle_name=middle_name,
        suffix=suffix,
        gender=gender,
        civil_status=civil_status,
        emp_status=emp_status,
        department_id=dept_id,
        branch_id=br_id,
        user_id=u_id,
        supervisor_id=sup_id,
        position=position,
        emp_no=emp_no
    )
    service.update_employee(db, employee_id, employee_in)
    return RedirectResponse(url="/employees/", status_code=status.HTTP_303_SEE_OTHER)

@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    service.delete_employee(db, employee_id)
    return HTMLResponse(content="", status_code=status.HTTP_200_OK)
