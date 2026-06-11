from sqlalchemy.orm import Session
from .model import Role
from .schema import RoleCreate, RoleUpdate
from app.modules.permissions.model import Permission

def get_role(db: Session, role_id: int):
    return db.query(Role).filter(Role.id == role_id).first()

def get_role_by_name(db: Session, name: str):
    return db.query(Role).filter(Role.name == name).first()

def get_roles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Role).offset(skip).limit(limit).all()

def create_role(db: Session, role: RoleCreate):
    db_role = Role(name=role.name, description=role.description)
    if role.permission_ids:
        permissions = db.query(Permission).filter(Permission.id.in_(role.permission_ids)).all()
        db_role.permissions = permissions
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def update_role(db: Session, role_id: int, role: RoleUpdate):
    db_role = get_role(db, role_id)
    if not db_role:
        return None
    
    update_data = role.model_dump(exclude_unset=True)
    permission_ids = update_data.pop("permission_ids", None)
    
    for key, value in update_data.items():
        setattr(db_role, key, value)
    
    if permission_ids is not None:
        permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        db_role.permissions = permissions
    
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def delete_role(db: Session, role_id: int):
    db_role = get_role(db, role_id)
    if not db_role:
        return None
    db.delete(db_role)
    db.commit()
    return db_role
