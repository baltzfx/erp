from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import date

# Enums
class GenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class CivilStatusEnum(str, Enum):
    SINGLE = "SINGLE"
    MARRIED = "MARRIED"
    WIDOWED = "WIDOWED"
    DIVORCED = "DIVORCED"
    SEPARATED = "SEPARATED"

class EmpStatusEnum(str, Enum):
    PROBATIONARY = "PROBATIONARY"
    REGULAR = "REGULAR"
    CONTRACTUAL = "CONTRACTUAL"
    TERMINATED = "TERMINATED"
    RESIGNED = "RESIGNED"

class PayrollFreqEnum(str, Enum):
    MONTHLY = "MONTHLY"
    SEMI_MONTHLY = "SEMI_MONTHLY"
    WEEKLY = "WEEKLY"

# Emergency Contact Schemas
class EmergencyContactBase(BaseModel):
    contact_person: str
    mobile_number: str
    relationship_to_emp: Optional[str] = None

class EmergencyContactCreate(EmergencyContactBase):
    pass

class EmergencyContact(EmergencyContactBase):
    id: int
    employee_id: int
    
    model_config = ConfigDict(from_attributes=True)

# Payroll Config Schemas
class EmployeePayrollConfigBase(BaseModel):
    salary: Optional[float] = None
    payroll_frequency: PayrollFreqEnum = PayrollFreqEnum.SEMI_MONTHLY
    bank_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    tin_no: Optional[str] = None
    sss_no: Optional[str] = None
    pagibig_no: Optional[str] = None
    philhealth_no: Optional[str] = None
    national_id_no: Optional[str] = None

class EmployeePayrollConfigCreate(EmployeePayrollConfigBase):
    pass

class EmployeePayrollConfig(EmployeePayrollConfigBase):
    id: int
    employee_id: int
    
    model_config = ConfigDict(from_attributes=True)

# Employee Schemas
class EmployeeBase(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    suffix: Optional[str] = None
    gender: Optional[GenderEnum] = None
    date_of_birth: Optional[date] = None
    civil_status: Optional[CivilStatusEnum] = None
    email: EmailStr
    phone: Optional[str] = None
    current_address: Optional[str] = None
    provincial_address: Optional[str] = None
    emp_no: Optional[str] = None
    biometric_id: Optional[str] = None
    position: Optional[str] = None
    class_type: Optional[str] = None
    sub_class: Optional[str] = None
    department_id: Optional[int] = None
    shift_id: Optional[int] = None
    branch_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    emp_status: Optional[EmpStatusEnum] = None
    hire_date: Optional[date] = None
    date_reg_contract: Optional[date] = None
    educational_attainment: Optional[str] = None
    recommended_by: Optional[str] = None
    is_active: bool = True
    user_id: Optional[int] = None
    # Payroll & Statutory (Flattened for Form Handling)
    salary: Optional[float] = None
    payroll_frequency: PayrollFreqEnum = PayrollFreqEnum.SEMI_MONTHLY
    bank_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    tin_no: Optional[str] = None
    sss_no: Optional[str] = None
    pagibig_no: Optional[str] = None
    philhealth_no: Optional[str] = None
    national_id_no: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    suffix: Optional[str] = None
    gender: Optional[GenderEnum] = None
    date_of_birth: Optional[date] = None
    civil_status: Optional[CivilStatusEnum] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    current_address: Optional[str] = None
    provincial_address: Optional[str] = None
    emp_no: Optional[str] = None
    biometric_id: Optional[str] = None
    position: Optional[str] = None
    class_type: Optional[str] = None
    sub_class: Optional[str] = None
    department_id: Optional[int] = None
    shift_id: Optional[int] = None
    branch_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    emp_status: Optional[EmpStatusEnum] = None
    hire_date: Optional[date] = None
    date_reg_contract: Optional[date] = None
    educational_attainment: Optional[str] = None
    recommended_by: Optional[str] = None
    is_active: Optional[bool] = None
    user_id: Optional[int] = None
    # Payroll & Statutory (Flattened for Form Handling)
    salary: Optional[float] = None
    payroll_frequency: Optional[PayrollFreqEnum] = None
    bank_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    tin_no: Optional[str] = None
    sss_no: Optional[str] = None
    pagibig_no: Optional[str] = None
    philhealth_no: Optional[str] = None
    national_id_no: Optional[str] = None

class EmployeeOut(EmployeeBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class BulkDeleteRequest(BaseModel):
    employee_ids: List[int]
