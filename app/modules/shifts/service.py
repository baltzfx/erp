from typing import List, Optional
from sqlalchemy.orm import Session
from .model import Shift
from .schema import ShiftCreate, ShiftUpdate

def get_shift(db: Session, shift_id: int) -> Optional[Shift]:
    return db.query(Shift).filter(Shift.id == shift_id).first()

def get_shifts(db: Session, skip: int = 0, limit: int = 100) -> List[Shift]:
    return db.query(Shift).offset(skip).limit(limit).all()

def create_shift(db: Session, shift: ShiftCreate) -> Shift:
    db_shift = Shift(**shift.model_dump())
    db.add(db_shift)
    db.commit()
    db.refresh(db_shift)
    return db_shift

def update_shift(db: Session, shift_id: int, shift: ShiftUpdate) -> Optional[Shift]:
    db_shift = get_shift(db, shift_id)
    if not db_shift:
        return None
    
    update_data = shift.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_shift, key, value)
    
    db.commit()
    db.refresh(db_shift)
    return db_shift

def delete_shift(db: Session, shift_id: int) -> Optional[Shift]:
    db_shift = get_shift(db, shift_id)
    if not db_shift:
        return None
    db.delete(db_shift)
    db.commit()
    return db_shift