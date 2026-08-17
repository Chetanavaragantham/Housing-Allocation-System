import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.database import get_db
from models import Student, Allocation, Room
from models.allocation import AllocationStatus
from models.schemas import AgentRunSchema
from agent.runner import run_allocation_agent
from datetime import datetime
import threading

router = APIRouter(prefix="/agent", tags=["Agent"])

# Store run results in memory for status checks
run_results = {}


@router.post("/run")
def trigger_agent_run(
    payload: AgentRunSchema,
    db: Session = Depends(get_db)
):
    run_id    = f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    start_time = datetime.utcnow()

    # Run agent in background thread
    def run_in_background():
        try:
            results = run_allocation_agent()
            run_results[run_id] = {
                "status":       "completed",
                "results":      results,
                "started_at":   start_time.isoformat(),
                "completed_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            run_results[run_id] = {
                "status": "failed",
                "error":  str(e)
            }

    run_results[run_id] = {
        "status":     "running",
        "started_at": start_time.isoformat()
    }

    thread = threading.Thread(target=run_in_background)
    thread.start()

    return {
        "status":  "success",
        "message": "Agent run started",
        "data": {
            "run_id":     run_id,
            "started_at": start_time.isoformat()
        }
    }


@router.get("/run/{run_id}")
def get_run_status(run_id: str):
    if run_id not in run_results:
        raise HTTPException(status_code=404, detail="Run ID not found")

    return {
        "status": "success",
        "data":   run_results[run_id]
    }


@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    total_students = db.query(Student).count()

    allocated = db.query(Allocation).filter(
        Allocation.status == AllocationStatus.allocated
    ).count()

    unresolved = db.query(Allocation).filter(
        Allocation.status == AllocationStatus.unresolved
    ).count()

    reallocated = db.query(Allocation).filter(
        Allocation.is_reallocated == True
    ).count()

    avg_score = db.query(
        func.avg(Allocation.compatibility_score)
    ).filter(
        Allocation.compatibility_score.isnot(None)
    ).scalar()

    return {
        "status": "success",
        "data": {
            "total_students":         total_students,
            "successfully_allocated": allocated,
            "allocation_rate":        round(allocated / total_students, 2) if total_students else 0,
            "average_compatibility":  round(float(avg_score), 2) if avg_score else 0,
            "total_reallocations":    reallocated,
            "unresolved_count":       unresolved
        }
    }