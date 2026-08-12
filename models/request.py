from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base
import enum


class RequestType(enum.Enum):
    application  = "application"
    room_change  = "room_change"


class RequestStatus(enum.Enum):
    pending    = "pending"
    processing = "processing"
    completed  = "completed"
    rejected   = "rejected"
    cancelled  = "cancelled"
    on_hold    = "on_hold"


class Request(Base):
    __tablename__ = "requests"

    id         = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)

    requested_roommate_1 = Column(Integer, ForeignKey("students.id"), nullable=True)
    requested_roommate_2 = Column(Integer, ForeignKey("students.id"), nullable=True)
    requested_roommate_3 = Column(Integer, ForeignKey("students.id"), nullable=True)

    request_type     = Column(Enum(RequestType), nullable=False)
    status           = Column(Enum(RequestStatus), default=RequestStatus.pending)
    rejection_reason = Column(Text, nullable=True)
    outcome_notes    = Column(Text, nullable=True)

    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    student    = relationship("Student", foreign_keys=[student_id], back_populates="requests")
    allocation = relationship("Allocation", back_populates="request", uselist=False)
    notifications = relationship("Notification", back_populates="request")