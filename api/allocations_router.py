import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models import Student, Allocation, Room
from models.allocation import AllocationStatus
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/allocations", tags=["Allocations"])


@router.get("/me")
def get_my_allocation(db: Session = Depends(get_db)):
    # Placeholder — student_id will come from JWT token in production
    student_id = 1

    allocation = db.query(Allocation).filter(
        Allocation.student_id == student_id,
        Allocation.status     == AllocationStatus.allocated
    ).first()

    if not allocation:
        return {
            "status":  "success",
            "data":    None,
            "message": "No allocation found. Your application is pending."
        }

    room = db.query(Room).filter(Room.id == allocation.room_id).first()

    return {
        "status": "success",
        "data": {
            "allocation_id":      allocation.id,
            "status":             allocation.status.value,
            "compatibility_score": allocation.compatibility_score,
            "is_reallocated":     allocation.is_reallocated,
            "allocated_at":       allocation.allocated_at.isoformat(),
            "room": {
                "room_number":      room.room_number,
                "building":         room.building,
                "apartment_number": room.apartment_number,
                "room_type":        room.room_type.value
            } if room else None
        }
    }


@router.get("/")
def get_all_allocations(
    status:   Optional[str] = None,
    building: Optional[str] = None,
    page:     int = 1,
    limit:    int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(Allocation)

    if status:
        query = query.filter(Allocation.status == status)

    if building:
        query = query.join(Room).filter(Room.building == building)

    total       = query.count()
    allocations = query.offset((page - 1) * limit).limit(limit).all()

    result = []
    for a in allocations:
        room    = db.query(Room).filter(Room.id == a.room_id).first()
        student = db.query(Student).filter(Student.id == a.student_id).first()
        result.append({
            "allocation_id":      a.id,
            "student_id":         student.student_id if student else None,
            "student_name":       f"{student.first_name} {student.last_name}" if student else None,
            "room_number":        room.room_number if room else None,
            "building":           room.building if room else None,
            "status":             a.status.value,
            "compatibility_score": a.compatibility_score,
            "allocated_at":       a.allocated_at.isoformat()
        })

    return {
        "status": "success",
        "total":  total,
        "page":   page,
        "limit":  limit,
        "data":   result
    }


@router.get("/unresolved")
def get_unresolved(db: Session = Depends(get_db)):
    allocations = db.query(Allocation).filter(
        Allocation.status == AllocationStatus.unresolved
    ).all()

    result = []
    for a in allocations:
        student = db.query(Student).filter(Student.id == a.student_id).first()
        result.append({
            "allocation_id": a.id,
            "student_id":    student.student_id if student else None,
            "student_name":  f"{student.first_name} {student.last_name}" if student else None,
            "status":        a.status.value,
            "allocated_at":  None
        })

    return {
        "status": "success",
        "total":  len(result),
        "data":   result
    }


@router.patch("/{allocation_id}/manual")
def manual_assignment(
    allocation_id: int,
    room_id:       int,
    override_reason: str,
    db: Session = Depends(get_db)
):
    allocation = db.query(Allocation).filter(
        Allocation.id == allocation_id
    ).first()

    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")

    room = db.query(Room).filter(Room.id == room_id).first()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if room.is_occupied:
        raise HTTPException(status_code=409, detail="Room is already occupied")

    if not room.is_rent_ready:
        raise HTTPException(status_code=409, detail="Room is not rent ready")

    # Update allocation
    allocation.room_id       = room_id
    allocation.status        = AllocationStatus.allocated
    allocation.is_reallocated = True
    allocation.allocated_at  = datetime.utcnow()

    # Update room
    room.is_occupied = True

    # Update student
    student = db.query(Student).filter(
        Student.id == allocation.student_id
    ).first()
    student.is_allocated = True

    db.commit()

    return {
        "status":  "success",
        "message": f"Student manually assigned to room {room.room_number}",
        "data": {
            "allocation_id": allocation.id,
            "room_number":   room.room_number,
            "building":      room.building,
            "status":        allocation.status.value
        }
    }