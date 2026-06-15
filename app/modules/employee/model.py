from typing import Optional
from sqlalchemy import Boolean, Column, Date, Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import backref, relationship, validates

from app.shared.models import BaseModel
from .schema import CivilStatusEnum, EmpStatusEnum, GenderEnum, PayrollFreqEnum


class Employee(BaseModel):
    """Complete Employee model integrated with ERP sub-modules"""
    
    __tablename__ = "employee"
    
    # System Identity Links
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    emp_no = Column(String(50), unique=True, index=True, nullable=True)
    biometric_id = Column(String(50), unique=True, index=True, nullable=True)
    supervisor_id = Column(Integer, ForeignKey("employee.id"), nullable=True)
    
    # Personal Profile
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False)
    suffix = Column(String(10), nullable=True)
    gender = Column(Enum(GenderEnum), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    civil_status = Column(Enum(CivilStatusEnum), nullable=True)
    
    # Contact Information
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    current_address = Column(String(255), nullable=True)
    provincial_address = Column(String(255), nullable=True)
    
    # Employment Details
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    class_type = Column(String(100), nullable=True)  # Core categorization
    sub_class = Column(String(100), nullable=True)    # Branch sub-grouping
    position = Column(String(100), nullable=True)      # Specific structural job title
    emp_status = Column(Enum(EmpStatusEnum), nullable=True)
    hire_date = Column(Date, nullable=True)
    date_reg_contract = Column(Date, nullable=True)    # Regularization date tracking
    is_active = Column(Boolean, default=True, index=True)
    
    # Background & Referrals
    educational_attainment = Column(String(100), nullable=True)
    recommended_by = Column(String(100), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="employee")
    department = relationship("Department", back_populates="employees")
    branch = relationship("Branch", back_populates="employees")
    # assets = relationship("Asset", back_populates="employee")
    # attendances = relationship("Attendance", back_populates="employee")
    # leave_requests = relationship("LeaveRequest", back_populates="employee")
    # overtime_requests = relationship("OvertimeRequest", back_populates="employee")
    
    # Self-referencing link for dynamic multi-level management tracking
    subordinates = relationship("Employee", backref=backref("supervisor", remote_side="Employee.id"))
    
    # Split Extensions for structural isolation
    payroll_config = relationship("EmployeePayrollConfig", uselist=False, back_populates="employee", cascade="all, delete-orphan", single_parent=True)
    emergency_contacts = relationship("EmergencyContact", back_populates="employee", cascade="all, delete-orphan")

    @property
    def salary(self):
        if self.payroll_config and self.payroll_config.salary is not None:
            return float(self.payroll_config.salary)
        return None
    
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
    
    employee_id = Column(Integer, ForeignKey("employee.id", ondelete="CASCADE"), unique=True, nullable=False)
    salary = Column(Numeric(10, 2), nullable=True)
    payroll_frequency = Column(Enum(PayrollFreqEnum), default=PayrollFreqEnum.SEMI_MONTHLY)
    bank_name = Column(String(100), nullable=True)
    bank_account_no = Column(String(50), nullable=True)
    
    # Statutory Registrations
    tin_no = Column(String(30), nullable=True)
    sss_no = Column(String(30), nullable=True)
    pagibig_no = Column(String(30), nullable=True)
    philhealth_no = Column(String(30), nullable=True)
    national_id_no = Column(String(50), nullable=True)
    
    employee = relationship("Employee", back_populates="payroll_config")


class EmergencyContact(BaseModel):
    """Dynamic multiple options list for Emergency Profile records"""
    
    __tablename__ = "employee_emergency_contact"
    
    employee_id = Column(Integer, ForeignKey("employee.id", ondelete="CASCADE"), nullable=False)
    contact_person = Column(String(150), nullable=False)
    mobile_number = Column(String(50), nullable=False)
    relationship_to_emp = Column(String(50), nullable=True)
    
    employee = relationship("Employee", back_populates="emergency_contacts")
