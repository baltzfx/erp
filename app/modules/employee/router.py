import csv
import io
from datetime import date
from typing import Optional, Annotated, List, Any
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.templates import templates
from app.core.database import get_db
from app.modules.employee import service, schema
from app.api import deps
from app.modules.users.model import User
from app.modules.department import service as dept_service
from app.modules.branch import service as branch_service
from app.modules.users import crud as user_service
from app.modules.shifts import service as shift_service

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
    shifts = shift_service.get_shifts(db)
    
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="employee/templates/create-employee.html",
        context={
            "shifts": shifts,
            "theme": theme, 
            "user": current_user,
            "departments": departments,
            "branches": branches,
            "users": users,
            "supervisors": supervisors,
            "genders": schema.GenderEnum,
            "civil_statuses": schema.CivilStatusEnum,
            "emp_statuses": schema.EmpStatusEnum,
            "payroll_frequencies": schema.PayrollFreqEnum
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
    date_of_birth: Annotated[Optional[date], Form()] = None,
    civil_status: Annotated[Optional[schema.CivilStatusEnum], Form()] = None,
    phone: Annotated[Optional[str], Form()] = None,
    current_address: Annotated[Optional[str], Form()] = None,
    provincial_address: Annotated[Optional[str], Form()] = None,
    emp_status: Annotated[Optional[schema.EmpStatusEnum], Form()] = None,
    department_id: Annotated[Optional[int], Form()] = None,
    shift_id: Annotated[Optional[int], Form()] = None,
    branch_id: Annotated[Optional[int], Form()] = None,
    user_id: Annotated[Optional[int], Form()] = None,
    supervisor_id: Annotated[Optional[int], Form()] = None,
    position: Annotated[Optional[str], Form()] = None,
    emp_no: Annotated[Optional[str], Form()] = None,
    biometric_id: Annotated[Optional[str], Form()] = None,
    class_type: Annotated[Optional[str], Form()] = None,
    sub_class: Annotated[Optional[str], Form()] = None,
    hire_date: Annotated[Optional[date], Form()] = None,
    date_reg_contract: Annotated[Optional[date], Form()] = None,
    educational_attainment: Annotated[Optional[str], Form()] = None,
    recommended_by: Annotated[Optional[str], Form()] = None,
    salary: Annotated[Optional[float], Form()] = None,
    payroll_frequency: Annotated[Optional[schema.PayrollFreqEnum], Form()] = None,
    bank_name: Annotated[Optional[str], Form()] = None,
    bank_account_no: Annotated[Optional[str], Form()] = None,
    tin_no: Annotated[Optional[str], Form()] = None,
    sss_no: Annotated[Optional[str], Form()] = None,
    pagibig_no: Annotated[Optional[str], Form()] = None,
    philhealth_no: Annotated[Optional[str], Form()] = None,
    national_id_no: Annotated[Optional[str], Form()] = None
):
    form_data = locals()
    form_data.pop("db")
    form_data.pop("current_user")
    employee_in = schema.EmployeeCreate(**form_data)
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
    shifts = shift_service.get_shifts(db)
    
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="employee/templates/edit-employee.html",
        context={
            "shifts": shifts,
            "employee": employee, 
            "theme": theme, 
            "user": current_user,
            "departments": departments,
            "branches": branches,
            "users": users,
            "supervisors": supervisors,
            "genders": schema.GenderEnum,
            "civil_statuses": schema.CivilStatusEnum,
            "emp_statuses": schema.EmpStatusEnum,
            "payroll_frequencies": schema.PayrollFreqEnum
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
    date_of_birth: Annotated[Optional[date], Form()] = None,
    civil_status: Annotated[Optional[schema.CivilStatusEnum], Form()] = None,
    phone: Annotated[Optional[str], Form()] = None,
    current_address: Annotated[Optional[str], Form()] = None,
    provincial_address: Annotated[Optional[str], Form()] = None,
    emp_status: Annotated[Optional[schema.EmpStatusEnum], Form()] = None,
    department_id: Annotated[Optional[int], Form()] = None,
    shift_id: Annotated[Optional[int], Form()] = None,
    branch_id: Annotated[Optional[int], Form()] = None,
    user_id: Annotated[Optional[int], Form()] = None,
    supervisor_id: Annotated[Optional[int], Form()] = None,
    position: Annotated[Optional[str], Form()] = None,
    emp_no: Annotated[Optional[str], Form()] = None,
    biometric_id: Annotated[Optional[str], Form()] = None,
    class_type: Annotated[Optional[str], Form()] = None,
    sub_class: Annotated[Optional[str], Form()] = None,
    hire_date: Annotated[Optional[date], Form()] = None,
    date_reg_contract: Annotated[Optional[date], Form()] = None,
    educational_attainment: Annotated[Optional[str], Form()] = None,
    recommended_by: Annotated[Optional[str], Form()] = None,
    salary: Annotated[Optional[float], Form()] = None,
    payroll_frequency: Annotated[Optional[schema.PayrollFreqEnum], Form()] = None,
    bank_name: Annotated[Optional[str], Form()] = None,
    bank_account_no: Annotated[Optional[str], Form()] = None,
    tin_no: Annotated[Optional[str], Form()] = None,
    sss_no: Annotated[Optional[str], Form()] = None,
    pagibig_no: Annotated[Optional[str], Form()] = None,
    philhealth_no: Annotated[Optional[str], Form()] = None,
    national_id_no: Annotated[Optional[str], Form()] = None
):
    form_data = locals()
    form_data.pop("db")
    form_data.pop("current_user")
    form_data.pop("employee_id")
    employee_in = schema.EmployeeUpdate(**form_data)
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

@router.get("/export/list")
def export_employees(db: Annotated[Session, Depends(get_db)]):
    employees = service.get_employees(db, limit=1000) # Adjust limit as needed
    
    output = io.StringIO()
    writer = csv.writer(output)
    # Define headers based on Employee model fields
    writer.writerow([
        "id", "emp_no", "biometric_id", "first_name", "middle_name", "last_name", "suffix",
        "gender", "date_of_birth", "civil_status", "email", "phone", "current_address",
        "provincial_address", "branch_id", "department_id", "shift_id", "class_type", "sub_class",
        "position", "emp_status", "hire_date", "date_reg_contract", "is_active",
        "educational_attainment", "recommended_by", "user_id", "supervisor_id",
        # Payroll config fields (if directly accessible or joined)
        "salary", "payroll_frequency", "bank_name", "bank_account_no",
        "tin_no", "sss_no", "pagibig_no", "philhealth_no", "national_id_no"
    ])
    
    for emp in employees:
        row_data: List[Any] = [
            emp.id, emp.emp_no if emp.emp_no is not None else "", emp.biometric_id if emp.biometric_id is not None else "", emp.first_name, emp.middle_name if emp.middle_name is not None else "", emp.last_name, emp.suffix if emp.suffix is not None else "",
            emp.gender.value if emp.gender is not None else "", emp.date_of_birth.isoformat() if emp.date_of_birth is not None else "", emp.civil_status.value if emp.civil_status is not None else "",
            emp.email, emp.phone if emp.phone is not None else "", emp.current_address if emp.current_address is not None else "", emp.provincial_address if emp.provincial_address is not None else "",
            emp.branch_id if emp.branch_id is not None else "", emp.department_id if emp.department_id is not None else "", emp.shift_id if emp.shift_id is not None else "", emp.class_type if emp.class_type is not None else "", emp.sub_class if emp.sub_class is not None else "",
            emp.position if emp.position is not None else "", emp.emp_status.value if emp.emp_status is not None else "", emp.hire_date.isoformat() if emp.hire_date is not None else "",
            emp.date_reg_contract.isoformat() if emp.date_reg_contract is not None else "", emp.is_active,
            emp.educational_attainment if emp.educational_attainment is not None else "", emp.recommended_by if emp.recommended_by is not None else "", emp.user_id if emp.user_id is not None else "", emp.supervisor_id if emp.supervisor_id is not None else ""
        ]

        # Handle payroll config fields
        if emp.payroll_config:
            payroll_config = emp.payroll_config
            row_data.extend([
                float(payroll_config.salary) if payroll_config.salary is not None else "",
                payroll_config.payroll_frequency.value,
                payroll_config.bank_name if payroll_config.bank_name is not None else "",
                payroll_config.bank_account_no if payroll_config.bank_account_no is not None else "",
                payroll_config.tin_no if payroll_config.tin_no is not None else "",
                payroll_config.sss_no if payroll_config.sss_no is not None else "",
                payroll_config.pagibig_no if payroll_config.pagibig_no is not None else "",
                payroll_config.philhealth_no if payroll_config.philhealth_no is not None else "",
                payroll_config.national_id_no if payroll_config.national_id_no is not None else ""
            ])
        else:
            # Append empty strings for all 9 payroll fields if no payroll_config
            row_data.extend([""] * 9)
        
        writer.writerow(row_data)
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employees_export.csv"}
    )

@router.get("/export/template")
def export_employee_template():
    output = io.StringIO()
    writer = csv.writer(output)
    # Define headers for the template, matching schema fields
    writer.writerow([
        "first_name", "middle_name", "last_name", "suffix", "gender", "date_of_birth",
        "civil_status", "email", "phone", "current_address", "provincial_address",
        "emp_no", "biometric_id", "position", "class_type", "sub_class", "shift_id",
        "department_id", "branch_id", "supervisor_id", "emp_status", "hire_date",
        "date_reg_contract", "educational_attainment", "recommended_by", "is_active",
        "user_id", "salary", "payroll_frequency", "bank_name", "bank_account_no",
        "tin_no", "sss_no", "pagibig_no", "philhealth_no", "national_id_no"
    ])
    # Example row for guidance
    writer.writerow([
        "Jane", "P.", "Doe", "Jr.", "FEMALE", "1990-01-15", "SINGLE",
        "jane.doe@example.com", "09171234567", "123 Main St, City", "456 Rural Rd, Province",
        "EMP-002", "BIO-5678", "Software Engineer", "Core", "Backend",
        "1", "1", "1", "", "REGULAR", "2020-03-01", "2020-09-01", "BS Computer Science", "HR Dept", "True",
        "", "50000.00", "MONTHLY", "BDO", "1234567890",
        "123-456-789-000", "00-1234567-8", "123456789012", "123456789012", "NID-123456789"
    ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employee_import_template.csv"}
    )

@router.post("/import")
async def import_employees(
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...)
) -> JSONResponse:
    content = await file.read()
    try:
        stream = io.StringIO(content.decode("utf-8"))
    except UnicodeDecodeError:
        stream = io.StringIO(content.decode("latin-1"))
        
    reader = csv.DictReader(stream)
    
    imported_count = 0
    errors: list[str] = []
    
    for row in reader:
        try:
            # Convert string values from CSV to appropriate types for schema
            # Handle optional fields and enums
            # ... (logic to parse row into employee_in schema.EmployeeCreate)
            employee_in_data = {k: v for k, v in row.items() if k in schema.EmployeeCreate.model_fields}
            # Manually convert enums and dates
            if 'gender' in employee_in_data and employee_in_data['gender']: employee_in_data['gender'] = schema.GenderEnum[employee_in_data['gender'].upper()]
            if 'civil_status' in employee_in_data and employee_in_data['civil_status']: employee_in_data['civil_status'] = schema.CivilStatusEnum[employee_in_data['civil_status'].upper()]
            if 'emp_status' in employee_in_data and employee_in_data['emp_status']: employee_in_data['emp_status'] = schema.EmpStatusEnum[employee_in_data['emp_status'].upper()]
            if 'payroll_frequency' in employee_in_data and employee_in_data['payroll_frequency']: employee_in_data['payroll_frequency'] = schema.PayrollFreqEnum[employee_in_data['payroll_frequency'].upper()]
            if 'date_of_birth' in employee_in_data and employee_in_data['date_of_birth']: employee_in_data['date_of_birth'] = date.fromisoformat(employee_in_data['date_of_birth'])
            if 'hire_date' in employee_in_data and employee_in_data['hire_date']: employee_in_data['hire_date'] = date.fromisoformat(employee_in_data['hire_date'])
            if 'date_reg_contract' in employee_in_data and employee_in_data['date_reg_contract']: employee_in_data['date_reg_contract'] = date.fromisoformat(employee_in_data['date_reg_contract'])
            if 'is_active' in employee_in_data: employee_in_data['is_active'] = employee_in_data['is_active'].lower() == 'true'
            
            # Convert numeric and ID fields to satisfy type checker
            if 'salary' in employee_in_data and employee_in_data['salary']:
                employee_in_data['salary'] = float(employee_in_data['salary'])
            
            for field in ['department_id', 'branch_id', 'user_id', 'supervisor_id', 'shift_id']:
                if field in employee_in_data and employee_in_data[field]:
                    employee_in_data[field] = int(employee_in_data[field])

            employee_in = schema.EmployeeCreate.model_validate(employee_in_data)
            
            existing_employee = service.get_employee_by_email(db, email=employee_in.email)
            if existing_employee:
                service.update_employee(db, existing_employee.id, schema.EmployeeUpdate(**employee_in.model_dump()))
            else:
                service.create_employee(db, employee_in)
            imported_count += 1
        except Exception as e:
            errors.append(f"Error importing employee {row.get('email', row.get('emp_no', 'unknown'))}: {str(e)}")
            
    return JSONResponse(
        content={"status": "success", "imported": imported_count, "errors": errors},
        headers={"HX-Redirect": "/employees/"}
    )

@router.post("/bulk-delete")
async def bulk_delete_employees(
    request_data: schema.BulkDeleteRequest, # Use the new schema
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
) -> dict[str, Any]:
    # Add authorization check if needed
    # if not current_user.is_superuser:
    #     raise HTTPException(status_code=403, detail="Not authorized")
    
    deleted_count = service.delete_employees_bulk(db, request_data.employee_ids)
    return {"status": "success", "deleted": deleted_count}
