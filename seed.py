from app.core.database import SessionLocal, engine
from app.shared.models import BaseModel
from app.modules.users import crud, schema
# Import all models to ensure they are registered with BaseModel.metadata
from app.modules.users.model import User
from app.modules.roles.model import Role
from app.modules.employee.model import Employee
from app.modules.branch.model import Branch
from app.modules.department.model import Department
from app.modules.shifts.model import Shift
from app.modules.attendance.model import Attendance
from app.modules.leave.model import LeaveRequest
from app.modules.holiday.model import Holiday

def seed_db():
    # Create tables
    BaseModel.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Delete existing admin if it exists to refresh hash
        admin = crud.get_user_by_email(db, "admin@example.com")
        if admin:
            db.delete(admin)
            db.commit()
            print("Deleted old admin user")
            
        user_in = schema.UserCreate(
            email="admin@example.com",
            username="admin",
            password="password123",
            first_name="Admin",
            last_name="User",
            is_superuser=True
        )
        crud.create_user(db, user_in)
        print("Admin user created with Argon2")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
