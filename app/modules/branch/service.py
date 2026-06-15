from sqlalchemy.orm import Session
from .model import Branch
from .schema import BranchCreate, BranchUpdate

def get_branch(db: Session, branch_id: int):
    return db.query(Branch).filter(Branch.id == branch_id).first()

def get_branch_by_name(db: Session, name: str):
    return db.query(Branch).filter(Branch.name == name).first()

def get_branches(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Branch).offset(skip).limit(limit).all()

def create_branch(db: Session, branch: BranchCreate):
    db_branch = Branch(name=branch.name, description=branch.description)
    db.add(db_branch)
    db.commit()
    db.refresh(db_branch)
    return db_branch

def update_branch(db: Session, branch_id: int, branch: BranchUpdate):
    db_branch = get_branch(db, branch_id)
    if not db_branch:
        return None
    
    update_data = branch.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_branch, key, value)
    
    db.add(db_branch)
    db.commit()
    db.refresh(db_branch)
    return db_branch

def delete_branch(db: Session, branch_id: int):
    db_branch = get_branch(db, branch_id)
    if not db_branch:
        return None
    db.delete(db_branch)
    db.commit()
    return db_branch
