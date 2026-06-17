from sqlalchemy.orm import Session
import datetime
from typing import Optional
from .model import Attendance
from .schema import AttendanceCreate, AttendanceUpdate
from app.modules.employee.model import Employee

def get_attendance(db: Session, attendance_id: int) -> Optional[Attendance]:
    return db.query(Attendance).filter(Attendance.id == attendance_id).first()

def get_attendances(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Attendance).offset(skip).limit(limit).all()

def get_employee_attendance(db: Session, employee_id: int, start_date: Optional[datetime.date] = None, end_date: Optional[datetime.date] = None):
    query = db.query(Attendance).filter(Attendance.employee_id == employee_id)
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)
    return query.all()

def get_today_attendance(db: Session, employee_id: int) -> Optional[Attendance]:
    today = datetime.date.today()
    return db.query(Attendance).filter(
        Attendance.employee_id == employee_id,
        Attendance.date == today
    ).first()

def calculate_attendance_metrics(attendance: Attendance, employee: Employee):
    """Calculates late, undertime, overtime, and net work minutes based on shift."""
    # 1. Late Calculation (Only requires check_in)
    if attendance.check_in and employee.shift_start:
        shift_start_dt = datetime.datetime.combine(attendance.date, employee.shift_start)
        # Using max(0, ...) simplifies the if/else logic
        attendance.late_minutes = max(0, int((attendance.check_in - shift_start_dt).total_seconds() / 60))
    else:
        attendance.late_minutes = 0

    # Exit if attendance is incomplete
    if not attendance.check_in or not attendance.check_out:
        return

    # 2. Total Duration
    duration = (attendance.check_out - attendance.check_in).total_seconds() / 60
    attendance.total_minutes = int(duration)

    # 3. Undertime & Overtime Calculation (Requires shift_end)
    if employee.shift_end:
        shift_end_dt = datetime.datetime.combine(attendance.date, employee.shift_end)
        
        # Undertime: Clocked out before shift ends
        attendance.undertime_minutes = max(0, int((shift_end_dt - attendance.check_out).total_seconds() / 60))
            
        # Overtime: Clocked out after shift ends
        attendance.overtime_minutes = max(0, int((attendance.check_out - shift_end_dt).total_seconds() / 60))

    # 4. Work Minutes (Net Work)
    # Simple rule: Total - Break (if > 5 hours, subtract 1 hour)
    work_mins = attendance.total_minutes or 0
    if work_mins > 300: # 5 hours
        work_mins -= 60 # 1 hour lunch
    attendance.work_minutes = max(0, work_mins)

def create_attendance(db: Session, attendance: AttendanceCreate):
    db_attendance = Attendance(**attendance.model_dump())
    
    # Fetch employee for shift info
    employee = db.query(Employee).filter(Employee.id == db_attendance.employee_id).first()
    if employee:
        calculate_attendance_metrics(db_attendance, employee)
        
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

def update_attendance(db: Session, attendance_id: int, attendance: AttendanceUpdate):
    db_attendance = get_attendance(db, attendance_id)
    if not db_attendance:
        return None
    
    update_data = attendance.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_attendance, key, value)
    
    # Fetch employee for shift info
    employee = db.query(Employee).filter(Employee.id == db_attendance.employee_id).first()
    if employee:
        calculate_attendance_metrics(db_attendance, employee)
    
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

def delete_attendance(db: Session, attendance_id: int):
    db_attendance = get_attendance(db, attendance_id)
    if not db_attendance:
        return None
    db.delete(db_attendance)
    db.commit()
    return db_attendance
