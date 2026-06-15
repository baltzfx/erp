from sqlalchemy.orm import Session
from .model import Department
from .schema import DepartmentCreate, DepartmentUpdate

def get_department(db: Session, department_id: int):
    return db.query(Department).filter(Department.id == department_id).first()

def get_department_by_name(db: Session, name: str):
    return db.query(Department).filter(Department.name == name).first()

def get_departments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Department).offset(skip).limit(limit).all()

def create_department(db: Session, department: DepartmentCreate):
    db_department = Department(name=department.name, description=department.description)
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department

def update_department(db: Session, department_id: int, department: DepartmentUpdate):
    db_department = get_department(db, department_id)
    if not db_department:
        return None
    
    update_data = department.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_department, key, value)
    
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department

def delete_department(db: Session, department_id: int):
    db_department = get_department(db, department_id)
    if not db_department:
        return None
    db.delete(db_department)
    db.commit()
    return db_department
