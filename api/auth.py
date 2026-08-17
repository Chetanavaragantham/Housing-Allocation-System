import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from models import Student
from models.schemas import RegisterSchema, LoginSchema, TokenSchema
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# JWT settings
SECRET_KEY  = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM   = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire    = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register", status_code=201)
def register(payload: RegisterSchema, db: Session = Depends(get_db)):
    # Check if email already exists
    existing = db.query(Student).filter(
        Student.email == payload.email
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    # Check if student_id already exists
    existing_id = db.query(Student).filter(
        Student.student_id == payload.student_id
    ).first()
    if existing_id:
        raise HTTPException(
            status_code=409,
            detail="Student ID already registered"
        )

    # Create student — store hashed password in phone_number field for now
    # In production you'd have a separate passwords table
    student = Student(
        student_id    = payload.student_id,
        first_name    = payload.first_name,
        last_name     = payload.last_name,
        email         = payload.email,
        phone_number  = hash_password(payload.password),
        date_of_birth = payload.date_of_birth,
        gender        = payload.gender,
        intake_date   = payload.intake_date,
        is_allocated  = False
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    return {
        "status": "success",
        "message": "Account created successfully",
        "data": {
            "id":           student.id,
            "student_id":   student.student_id,
            "email":        student.email,
            "is_allocated": student.is_allocated
        }
    }


@router.post("/login")
def login(payload: LoginSchema, db: Session = Depends(get_db)):
    student = db.query(Student).filter(
        Student.email == payload.email
    ).first()

    if not student:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not verify_password(payload.password, student.phone_number):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token({
        "sub":  str(student.id),
        "role": "student"
    })

    return {
        "status":       "success",
        "access_token": token,
        "token_type":   "bearer",
        "role":         "student"
    }