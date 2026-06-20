from sqlalchemy.orm import Session, joinedload
from .model import OrgUnit
from .schema import OrgUnitCreate, OrgUnitUpdate

def get_org_unit(db: Session, org_unit_id: int):
    return db.query(OrgUnit).options(joinedload(OrgUnit.parent)).filter(OrgUnit.id == org_unit_id).first()

def get_org_unit_by_name(db: Session, name: str):
    return db.query(OrgUnit).filter(OrgUnit.name == name).first()

def get_org_units(db: Session, skip: int = 0, limit: int = 100):
    return db.query(OrgUnit).options(joinedload(OrgUnit.parent)).offset(skip).limit(limit).all()

def get_org_units_tree(db: Session):
    """Returns top-level units with their children loaded"""
    return db.query(OrgUnit).filter(OrgUnit.parent_id == None).options(joinedload(OrgUnit.children)).all()

def create_org_unit(db: Session, org_unit: OrgUnitCreate):
    db_org_unit = OrgUnit(**org_unit.model_dump())
    db.add(db_org_unit)
    db.commit()
    db.refresh(db_org_unit)
    return db_org_unit

def update_org_unit(db: Session, org_unit_id: int, org_unit: OrgUnitUpdate):
    db_org_unit = get_org_unit(db, org_unit_id)
    if not db_org_unit:
        return None
    
    update_data = org_unit.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_org_unit, key, value)
    
    db.commit()
    db.refresh(db_org_unit)
    return db_org_unit

def delete_org_unit(db: Session, org_unit_id: int):
    db_org_unit = get_org_unit(db, org_unit_id)
    if not db_org_unit:
        return None
    db.delete(db_org_unit)
    db.commit()
    return db_org_unit
