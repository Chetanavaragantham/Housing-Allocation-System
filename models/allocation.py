from sqlalchemy import Column, Integer, Float, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base
import enum


class AllocationStatus(enum.Enum):
    pending     = "pending"
    allocated   = "allocated"
    reallocated = "reallocated"
    unresolved  = "unresolved"


class Allocation(Base):
    __tablename__ = "allocations"

    id         = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    room_id    = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)

    status              = Column(Enum(AllocationStatus), default=AllocationStatus.pending)
    compatibility_score = Column(Float, nullable=True)
    is_reallocated      = Column(Boolean, default=False)
    allocated_at        = Column(DateTime(timezone=True), server_default=func.now())

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    student = relationship("Student", back_populates="allocations")
    room    = relationship("Room")
    request = relationship("Request", back_populates="allocation")