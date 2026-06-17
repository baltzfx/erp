from typing import List, Optional
from sqlalchemy.orm import Session
from .model import Holiday
from .schema import HolidayCreate, HolidayUpdate

def get_holiday(db: Session, holiday_id: int) -> Optional[Holiday]:
    return db.query(Holiday).filter(Holiday.id == holiday_id).first()

def get_holidays(db: Session, skip: int = 0, limit: int = 100) -> List[Holiday]:
    return db.query(Holiday).order_by(Holiday.date.asc()).offset(skip).limit(limit).all()

def create_holiday(db: Session, holiday: HolidayCreate) -> Holiday:
    db_holiday = Holiday(**holiday.model_dump())
    db.add(db_holiday)
    db.commit()
    db.refresh(db_holiday)
    return db_holiday

def update_holiday(db: Session, holiday_id: int, holiday: HolidayUpdate) -> Optional[Holiday]:
    db_holiday = get_holiday(db, holiday_id)
    if not db_holiday:
        return None
    
    update_data = holiday.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_holiday, key, value)
    
    db.commit()
    db.refresh(db_holiday)
    return db_holiday

def delete_holiday(db: Session, holiday_id: int) -> bool:
    db_holiday = get_holiday(db, holiday_id)
    if not db_holiday:
        return False
    db.delete(db_holiday)
    db.commit()
    return True