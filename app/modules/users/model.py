from sqlalchemy import String, Boolean, Index, ForeignKey
from typing import Optional, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import BaseModel

if TYPE_CHECKING:
    from app.modules.roles.model import Role
    from app.shared.models import Employee


class User(BaseModel):
    """User model"""
    
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    role_id: Mapped[Optional[int]] = mapped_column(ForeignKey("roles.id"), nullable=True)
    
    # Relationships
    role: Mapped[Optional["Role"]] = relationship("Role", back_populates="users")
    employee: Mapped[Optional["Employee"]] = relationship("Employee", back_populates="user", uselist=False)
    
    # @validates("email", "username")
    # def validate_lower(self, key, value):
    #     return self.to_lower(value)

    # @validates("first_name", "last_name")
    # def validate_proper(self, key, value):
    #     return self.to_proper(value)

    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_username", "username"),
        Index("idx_user_active", "is_active"),
    )
