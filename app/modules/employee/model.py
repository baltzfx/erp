from datetime import date, time
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Boolean, Date, Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, backref, relationship, validates

if TYPE_CHECKING:
    from app.modules.users.model import User
    from app.modules.department.model import Department
    from app.modules.branch.model import Branch
    from app.modules.attendance.model import Attendance
    from app.modules.shifts.model import Shift

from app.shared.models import BaseModel
from .schema import CivilStatusEnum, EmpStatusEnum, GenderEnum, PayrollFreqEnum


class Employee(BaseModel):
    """Complete Employee model integrated with ERP sub-modules"""
    
    __tablename__ = "employee"
    
    # System Identity Links
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    emp_no: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)
    biometric_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)
    supervisor_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("employee.id"), nullable=True)
    
    # Personal Profile
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    suffix: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    gender: Mapped[Optional[GenderEnum]] = mapped_column(Enum(GenderEnum), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    civil_status: Mapped[Optional[CivilStatusEnum]] = mapped_column(Enum(CivilStatusEnum), nullable=True)
    
    # Contact Information
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    current_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provincial_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Employment Details
    branch_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("branches.id"), nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)
    class_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Core categorization
    sub_class: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)    # Branch sub-grouping
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)      # Specific structural job title
    emp_status: Mapped[Optional[EmpStatusEnum]] = mapped_column(Enum(EmpStatusEnum), nullable=True)
    hire_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_reg_contract: Mapped[Optional[date]] = mapped_column(Date, nullable=True)    # Regularization date tracking
    shift_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("shifts.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Background & Referrals
    educational_attainment: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    recommended_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="employee")
    department: Mapped[Optional["Department"]] = relationship("Department", back_populates="employees")
    branch: Mapped[Optional["Branch"]] = relationship("Branch", back_populates="employees")
    attendances: Mapped[List["Attendance"]] = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")
    shift: Mapped[Optional["Shift"]] = relationship("Shift", back_populates="employees")
    
    # Self-referencing link for dynamic multi-level management tracking
    subordinates = relationship("Employee", backref=backref("supervisor", remote_side="Employee.id"))
    
    # Split Extensions for structural isolation
    payroll_config: Mapped[Optional["EmployeePayrollConfig"]] = relationship("EmployeePayrollConfig", uselist=False, back_populates="employee", cascade="all, delete-orphan", single_parent=True)
    emergency_contacts: Mapped[List["EmergencyContact"]] = relationship("EmergencyContact", back_populates="employee", cascade="all, delete-orphan")

    @property
    def salary(self):
        if self.payroll_config and self.payroll_config.salary is not None:
            return float(self.payroll_config.salary)
        return None

    @property
    def shift_start(self) -> Optional[time]:
        return self.shift.start_time if self.shift else None

    @property
    def shift_end(self) -> Optional[time]:
        return self.shift.end_time if self.shift else None
    
    @validates("first_name", "last_name", "middle_name", "suffix")
    def validate_proper(self, key: str, value: Optional[str]) -> Optional[str]:
        return self.to_proper(value) if value else value

    @validates("email")
    def validate_lower(self, key: str, value: Optional[str]) -> Optional[str]:
        return self.to_lower(value) if value else value

    @validates("phone")
    def validate_numbers(self, key: str, value: Optional[str]) -> Optional[str]:
        return self.to_numbers(value) if value else value

    __table_args__ = (
        Index("idx_employee_department", "department_id"),
        Index("idx_employee_branch", "branch_id"),
        Index("idx_employee_active", "is_active"),
    )


class EmployeePayrollConfig(BaseModel):
    """Isolated highly sensitive salary and statutory profile elements"""
    
    __tablename__ = "employee_payroll_config"
    
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employee.id", ondelete="CASCADE"), unique=True, nullable=False)
    salary: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    payroll_frequency: Mapped[PayrollFreqEnum] = mapped_column(Enum(PayrollFreqEnum), default=PayrollFreqEnum.SEMI_MONTHLY)
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_account_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Statutory Registrations
    tin_no: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    sss_no: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    pagibig_no: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    philhealth_no: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    national_id_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    employee: Mapped["Employee"] = relationship("Employee", back_populates="payroll_config")


class EmergencyContact(BaseModel):
    """Dynamic multiple options list for Emergency Profile records"""
    
    __tablename__ = "employee_emergency_contact"
    
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employee.id", ondelete="CASCADE"), nullable=False)
    contact_person: Mapped[str] = mapped_column(String(150), nullable=False)
    mobile_number: Mapped[str] = mapped_column(String(50), nullable=False)
    relationship_to_emp: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    employee: Mapped["Employee"] = relationship("Employee", back_populates="emergency_contacts")
