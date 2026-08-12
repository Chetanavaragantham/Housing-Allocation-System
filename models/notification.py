from sqlalchemy import Column, Integer, Text, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base
import enum


class NotificationType(enum.Enum):
    too_early         = "too_early"
    waiting_for_group = "waiting_for_group"
    group_unavailable = "group_unavailable"
    allocated         = "allocated"
    unresolved        = "unresolved"


class EmailStatus(enum.Enum):
    pending = "pending"
    sent    = "sent"
    failed  = "failed"


class Notification(Base):
    __tablename__ = "notifications"

    id         = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=True)

    type          = Column(Enum(NotificationType), nullable=False)
    message       = Column(Text, nullable=False)
    is_email_sent = Column(Enum(EmailStatus), default=EmailStatus.pending)
    sent_at       = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    student = relationship("Student", back_populates="notifications")
    request = relationship("Request", back_populates="notifications")