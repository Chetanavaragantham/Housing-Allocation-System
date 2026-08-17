import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models import Student, Request
from models.request import RequestStatus, RequestType
from models.schemas import CreateRequestSchema, UpdateRequestSchema, RequestResponseSchema
from datetime import datetime
from typing import List, Optional

router = APIRouter(prefix="/requests", tags=["Requests"])


@router.post("/", status_code=201)
def submit_request(
    payload: CreateRequestSchema,
    db: Session = Depends(get_db)
):
    # Check if student already has a pending request of same type
    # For now we use student_id 1 as placeholder — auth comes later
    # In production this comes from JWT token

    # Resolve roommate student IDs from student_id strings
    def resolve_roommate(student_id_str: Optional[str]):
        if not student_id_str:
            return None
        student = db.query(Student).filter(
            Student.student_id == student_id_str
        ).first()
        if not student:
            raise HTTPException(
                status_code=404,
                detail=f"Roommate with student ID {student_id_str} not found"
            )
        return student.id

    roommate_1 = resolve_roommate(payload.requested_roommate_1)
    roommate_2 = resolve_roommate(payload.requested_roommate_2)
    roommate_3 = resolve_roommate(payload.requested_roommate_3)

    request = Request(
        student_id           = 1,  # placeholder — will come from JWT
        request_type         = RequestType[payload.request_type.value],
        status               = RequestStatus.pending,
        requested_roommate_1 = roommate_1,
        requested_roommate_2 = roommate_2,
        requested_roommate_3 = roommate_3,
        submitted_at         = datetime.utcnow()
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    return {
        "status":  "success",
        "message": "Request submitted successfully",
        "data": {
            "id":           request.id,
            "request_type": request.request_type.value,
            "status":       request.status.value,
            "submitted_at": request.submitted_at.isoformat()
        }
    }


@router.patch("/{request_id}")
def update_request(
    request_id: int,
    payload: UpdateRequestSchema,
    db: Session = Depends(get_db)
):
    request = db.query(Request).filter(
        Request.id == request_id
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if request.status not in [RequestStatus.pending]:
        raise HTTPException(
            status_code=409,
            detail="Cannot edit a request that has already been processed"
        )

    def resolve_roommate(student_id_str: Optional[str]):
        if not student_id_str:
            return None
        student = db.query(Student).filter(
            Student.student_id == student_id_str
        ).first()
        if not student:
            raise HTTPException(
                status_code=404,
                detail=f"Roommate with student ID {student_id_str} not found"
            )
        return student.id

    if payload.requested_roommate_1 is not None:
        request.requested_roommate_1 = resolve_roommate(payload.requested_roommate_1)
    if payload.requested_roommate_2 is not None:
        request.requested_roommate_2 = resolve_roommate(payload.requested_roommate_2)
    if payload.requested_roommate_3 is not None:
        request.requested_roommate_3 = resolve_roommate(payload.requested_roommate_3)

    db.commit()
    db.refresh(request)

    return {
        "status":  "success",
        "message": "Request updated successfully",
        "data": {
            "id":         request.id,
            "updated_at": datetime.utcnow().isoformat()
        }
    }


@router.patch("/{request_id}/cancel")
def cancel_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    request = db.query(Request).filter(
        Request.id == request_id
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if request.status in [RequestStatus.completed]:
        raise HTTPException(
            status_code=409,
            detail="Cannot cancel a completed request"
        )

    request.status      = RequestStatus.cancelled
    request.processed_at = datetime.utcnow()
    db.commit()

    return {
        "status":  "success",
        "message": "Request cancelled successfully",
        "data": {
            "id":     request.id,
            "status": request.status.value
        }
    }


@router.get("/")
def get_all_requests(
    status: Optional[str] = None,
    request_type: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(Request)

    if status:
        query = query.filter(Request.status == status)
    if request_type:
        query = query.filter(Request.request_type == request_type)

    total    = query.count()
    requests = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "status": "success",
        "total":  total,
        "page":   page,
        "limit":  limit,
        "data": [
            {
                "id":           r.id,
                "student_id":   r.student_id,
                "request_type": r.request_type.value,
                "status":       r.status.value,
                "submitted_at": r.submitted_at.isoformat()
            }
            for r in requests
        ]
    }


@router.delete("/{request_id}")
def delete_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    request = db.query(Request).filter(
        Request.id == request_id
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    db.delete(request)
    db.commit()

    return {
        "status":  "success",
        "message": "Request deleted successfully"
    }