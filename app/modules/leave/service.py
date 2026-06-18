from typing import List, Optional
from sqlalchemy.orm import Session
from .model import LeaveRequest
from .schema import LeaveRequestCreate, LeaveRequestUpdate

def get_leave_request(db: Session, leave_request_id: int) -> Optional[LeaveRequest]:
    return db.query(LeaveRequest).filter(LeaveRequest.id == leave_request_id).first()

def get_leave_requests(db: Session, skip: int = 0, limit: int = 100) -> List[LeaveRequest]:
    return db.query(LeaveRequest).order_by(LeaveRequest.start_date.desc()).offset(skip).limit(limit).all()

def create_leave_request(db: Session, leave_request: LeaveRequestCreate) -> LeaveRequest:
    db_leave_request = LeaveRequest(**leave_request.model_dump())
    db.add(db_leave_request)
    db.commit()
    db.refresh(db_leave_request)
    return db_leave_request

def update_leave_request(db: Session, leave_request_id: int, leave_request: LeaveRequestUpdate) -> Optional[LeaveRequest]:
    db_leave_request = get_leave_request(db, leave_request_id)
    if not db_leave_request:
        return None
    
    update_data = leave_request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_leave_request, key, value)
    
    db.commit()
    db.refresh(db_leave_request)
    return db_leave_request

def delete_leave_request(db: Session, leave_request_id: int) -> bool:
    db_leave_request = get_leave_request(db, leave_request_id)
    if not db_leave_request:
        return False
    db.delete(db_leave_request)
    db.commit()
    return True
