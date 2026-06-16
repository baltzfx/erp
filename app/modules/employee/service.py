from typing import List
from sqlalchemy.orm import Session
from .model import Employee, EmployeePayrollConfig
from .schema import EmployeeCreate, EmployeeUpdate

def get_employee(db: Session, employee_id: int):
    return db.query(Employee).filter(Employee.id == employee_id).first()

def get_employee_by_email(db: Session, email: str):
    return db.query(Employee).filter(Employee.email == email).first()

def get_employees(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Employee).offset(skip).limit(limit).all()

def create_employee(db: Session, employee: EmployeeCreate):
    data = employee.model_dump()
    payroll_fields = ["salary", "payroll_frequency", "bank_name", "bank_account_no", 
                      "tin_no", "sss_no", "pagibig_no", "philhealth_no", "national_id_no"]
    payroll_data = {k: data.pop(k) for k in payroll_fields if k in data}
    
    db_employee = Employee(**data)
    db_employee.payroll_config = EmployeePayrollConfig(**payroll_data)
    
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

def update_employee(db: Session, employee_id: int, employee: EmployeeUpdate):
    db_employee = get_employee(db, employee_id)
    if not db_employee:
        return None
    
    update_data = employee.model_dump(exclude_unset=True)
    payroll_fields = ["salary", "payroll_frequency", "bank_name", "bank_account_no", 
                      "tin_no", "sss_no", "pagibig_no", "philhealth_no", "national_id_no"]
    payroll_data = {k: update_data.pop(k) for k in payroll_fields if k in update_data}
    
    for key, value in update_data.items():
        setattr(db_employee, key, value)
    
    if payroll_data:
        if not db_employee.payroll_config:
            db_employee.payroll_config = EmployeePayrollConfig(employee_id=employee_id)
        for key, value in payroll_data.items():
            setattr(db_employee.payroll_config, key, value)

    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

def delete_employee(db: Session, employee_id: int):
    db_employee = get_employee(db, employee_id)
    if not db_employee:
        return None
    db.delete(db_employee)
    db.commit()
    return db_employee

def delete_employees_bulk(db: Session, employee_ids: List[int]):
    """Deletes multiple employees by their IDs."""
    deleted_count = 0
    for employee_id in employee_ids:
        db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if db_employee:
            db.delete(db_employee)
            deleted_count += 1
    db.commit()
    return deleted_count
