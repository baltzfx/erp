from sqlalchemy.orm import Session
from .model import Permission
from .schema import PermissionCreate, PermissionUpdate

def get_permission(db: Session, permission_id: int):
    return db.query(Permission).filter(Permission.id == permission_id).first()

def get_permission_by_codename(db: Session, codename: str):
    return db.query(Permission).filter(Permission.codename == codename).first()

def get_permissions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Permission).offset(skip).limit(limit).all()

def create_permission(db: Session, permission: PermissionCreate):
    db_permission = Permission(
        name=permission.name, 
        codename=permission.codename,
        description=permission.description
    )
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

def update_permission(db: Session, permission_id: int, permission: PermissionUpdate):
    db_permission = get_permission(db, permission_id)
    if not db_permission:
        return None
    
    update_data = permission.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_permission, key, value)
    
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

def delete_permission(db: Session, permission_id: int):
    db_permission = get_permission(db, permission_id)
    if not db_permission:
        return None
    db.delete(db_permission)
    db.commit()
    return db_permission
