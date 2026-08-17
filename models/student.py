from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base
import enum


class Gender(enum.Enum):
    male   = "male"
    female = "female"
    other  = "other"


class Student(Base):
    __tablename__ = "students"

    id            = Column(Integer, primary_key=True, index=True)
    student_id    = Column(String, unique=True, nullable=False, index=True)
    first_name    = Column(String, nullable=False)
    last_name     = Column(String, nullable=False)
    email         = Column(String, unique=True, nullable=False)
    phone_number  = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender        = Column(Enum(Gender), nullable=True)
    intake_date   = Column(Date, nullable=True)
    is_allocated  = Column(Boolean, default=False)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    preference    = relationship(
        "StudentPreference",
        back_populates="student",
        foreign_keys="StudentPreference.student_id",
        uselist=False
    )
    allocations   = relationship("Allocation", back_populates="student")
    requests      = relationship(
        "Request",
        back_populates="student",
        foreign_keys="Request.student_id"
    )
    notifications = relationship("Notification", back_populates="student")