from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base
import enum


class SleepSchedule(enum.Enum):
    early_bird = "early_bird"
    night_owl  = "night_owl"


class StudyHabits(enum.Enum):
    quiet = "quiet"
    group = "group"


class Diet(enum.Enum):
    vegetarian     = "vegetarian"
    non_vegetarian = "non_vegetarian"
    vegan          = "vegan"


class StudentPreference(Base):
    __tablename__ = "student_preferences"

    id         = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, unique=True)

    requested_roommate_1 = Column(Integer, ForeignKey("students.id"), nullable=True)
    requested_roommate_2 = Column(Integer, ForeignKey("students.id"), nullable=True)
    requested_roommate_3 = Column(Integer, ForeignKey("students.id"), nullable=True)

    sleep_schedule  = Column(Enum(SleepSchedule), nullable=False)
    noise_tolerance = Column(Integer, nullable=False)  # 1–5
    cleanliness     = Column(Integer, nullable=False)  # 1–5
    study_habits    = Column(Enum(StudyHabits), nullable=False)
    diet            = Column(Enum(Diet), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    student = relationship("Student", foreign_keys=[student_id], back_populates="preferences")