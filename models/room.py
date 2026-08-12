from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Enum
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func
from db.database import Base
import enum


class RoomType(enum.Enum):
    private = "private"
    double  = "double"
    triple  = "triple"
    quad    = "quad"


class MaintenanceStatus(enum.Enum):
    not_applicable     = "not_applicable"
    pending_escalation = "pending_escalation"
    escalated          = "escalated"
    work_assigned      = "work_assigned"
    work_in_progress   = "work_in_progress"
    completed          = "completed"
    rent_ready         = "rent_ready"


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = (
        UniqueConstraint('building', 'room_number', name='uq_building_room'),
    )

    id               = Column(Integer, primary_key=True, index=True)
    room_number      = Column(String, nullable=False)
    building         = Column(String, nullable=False)
    apartment_number = Column(String, nullable=False)
    room_type        = Column(Enum(RoomType), nullable=False)
    is_occupied      = Column(Boolean, default=False)
    is_rent_ready    = Column(Boolean, default=False)
    room_issues      = Column(Text, nullable=True)
    maintenance_status = Column(
        Enum(MaintenanceStatus),
        default=MaintenanceStatus.not_applicable
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @property
    def is_available(self):
        return not self.is_occupied