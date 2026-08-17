from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class RequestTypeEnum(str, Enum):
    application = "application"
    room_change  = "room_change"


class GenderEnum(str, Enum):
    male   = "male"
    female = "female"
    other  = "other"


# ─────────────────────────────────────────────
# AUTH SCHEMAS
# ─────────────────────────────────────────────

class RegisterSchema(BaseModel):
    student_id:   str
    first_name:   str
    last_name:    str
    email:        str
    password:     str
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender:       Optional[GenderEnum] = None
    intake_date:  Optional[date] = None


class LoginSchema(BaseModel):
    email:    str
    password: str


class TokenSchema(BaseModel):
    access_token: str
    token_type:   str
    role:         str


# ─────────────────────────────────────────────
# STUDENT SCHEMAS
# ─────────────────────────────────────────────

class StudentResponseSchema(BaseModel):
    id:           int
    student_id:   str
    first_name:   str
    last_name:    str
    email:        str
    is_allocated: bool
    created_at:   datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# REQUEST SCHEMAS
# ─────────────────────────────────────────────

class CreateRequestSchema(BaseModel):
    request_type:         RequestTypeEnum
    requested_roommate_1: Optional[str] = None
    requested_roommate_2: Optional[str] = None
    requested_roommate_3: Optional[str] = None


class UpdateRequestSchema(BaseModel):
    requested_roommate_1: Optional[str] = None
    requested_roommate_2: Optional[str] = None
    requested_roommate_3: Optional[str] = None


class RequestResponseSchema(BaseModel):
    id:           int
    request_type: str
    status:       str
    submitted_at: datetime
    processed_at: Optional[datetime] = None
    outcome_notes: Optional[str] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# ALLOCATION SCHEMAS
# ─────────────────────────────────────────────

class RoomResponseSchema(BaseModel):
    room_number:      str
    building:         str
    apartment_number: str
    room_type:        str

    class Config:
        from_attributes = True


class AllocationResponseSchema(BaseModel):
    id:                  int
    status:              str
    compatibility_score: Optional[float] = None
    is_reallocated:      bool
    allocated_at:        datetime
    room:                Optional[RoomResponseSchema] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# AGENT SCHEMAS
# ─────────────────────────────────────────────

class AgentRunSchema(BaseModel):
    mode: str = "full"


class AgentRunResponseSchema(BaseModel):
    status:  str
    message: str


class AgentMetricsSchema(BaseModel):
    total_students:            int
    successfully_allocated:    int
    allocation_rate:           float
    average_compatibility:     float
    total_reallocations:       int
    unresolved_count:          int


# ─────────────────────────────────────────────
# STANDARD RESPONSE WRAPPER
# ─────────────────────────────────────────────

class StandardResponse(BaseModel):
    status:  str
    message: Optional[str] = None
    data:    Optional[dict] = None