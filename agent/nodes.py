import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from agent.state import HousingAgentState
from db.database import SessionLocal
from models import Student, StudentPreference, Room, Allocation, Request, Notification
from models.room import RoomType, MaintenanceStatus
from models.allocation import AllocationStatus
from models.request import RequestStatus
from models.notification import NotificationType, EmailStatus


# ─────────────────────────────────────────────
# NODE 1 — Load Request
# Loads the full request and student data into state
# ─────────────────────────────────────────────
def load_request_node(state: HousingAgentState) -> HousingAgentState:
    db = SessionLocal()
    try:
        request = db.query(Request).filter(
            Request.id == state["request_id"]
        ).first()

        student = db.query(Student).filter(
            Student.id == request.student_id
        ).first()

        preference = db.query(StudentPreference).filter(
            StudentPreference.student_id == student.id
        ).first()

        # Build roommate id list
        roommate_ids = []
        if preference:
            for attr in ["requested_roommate_1", "requested_roommate_2", "requested_roommate_3"]:
                val = getattr(preference, attr)
                if val:
                    roommate_ids.append(val)

        state["student_id"]    = student.id
        state["request_type"]  = request.request_type.value
        state["student_profile"] = {
            "id":             student.id,
            "student_id":     student.student_id,
            "first_name":     student.first_name,
            "last_name":      student.last_name,
            "email":          student.email,
            "sleep_schedule": preference.sleep_schedule.value if preference else None,
            "noise_tolerance": preference.noise_tolerance if preference else None,
            "cleanliness":    preference.cleanliness if preference else None,
            "study_habits":   preference.study_habits.value if preference else None,
        }
        state["roommate_ids"]        = roommate_ids
        state["has_roommate_request"] = len(roommate_ids) > 0
        state["current_node"]        = "load_request"
        state["attempts"]            = 0
        state["status"]              = "processing"
        state["notifications_sent"]  = []

        print(f"📋 Loaded request {state['request_id']} for student {student.first_name} {student.last_name}")
        return state

    finally:
        db.close()


# ─────────────────────────────────────────────
# NODE 2 — Validate Request
# Checks eligibility, 3-day buffer, roommate completeness
# ─────────────────────────────────────────────
def validate_request_node(state: HousingAgentState) -> HousingAgentState:
    db = SessionLocal()
    try:
        state["current_node"] = "validate_request"
        request = db.query(Request).filter(
            Request.id == state["request_id"]
        ).first()

        student = db.query(Student).filter(
            Student.id == state["student_id"]
        ).first()

        # Check 1 — student exists
        if not student:
            state["status"]       = "rejected"
            state["error_reason"] = "Student not found in system"
            return state

        # Check 2 — room change 3-day buffer
        if state["request_type"] == "room_change":
            allocation = db.query(Allocation).filter(
                Allocation.student_id == student.id,
                Allocation.status     == AllocationStatus.allocated
            ).first()

            if allocation:
                days_since = (datetime.utcnow() - allocation.allocated_at).days
                if days_since < 3:
                    state["status"]       = "on_hold"
                    state["error_reason"] = f"Only {days_since} days since allocation. Minimum 3 days required."
                    return state

        # Check 3 — validate roommate group completeness
        if state["has_roommate_request"]:
            all_submitted = True
            for roommate_id in state["roommate_ids"]:
                roommate_request = db.query(Request).filter(
                    Request.student_id   == roommate_id,
                    Request.request_type == request.request_type,
                    Request.status.in_([RequestStatus.pending, RequestStatus.processing])
                ).first()

                if not roommate_request:
                    all_submitted = False
                    break

            if not all_submitted:
                state["status"]        = "on_hold"
                state["error_reason"]  = "Waiting for all roommates to submit requests"
                state["group_validated"] = False
                return state

            state["group_validated"] = True

        state["status"] = "processing"
        print(f"✅ Request {state['request_id']} validated successfully")
        return state

    finally:
        db.close()
        
# ─────────────────────────────────────────────
# NODE 3 — Search Rooms
# Finds available rent-ready rooms
# Partial rooms first, empty rooms second
# ─────────────────────────────────────────────
def search_rooms_node(state: HousingAgentState) -> HousingAgentState:
    db = SessionLocal()
    try:
        state["current_node"] = "search_rooms"

        if state["has_roommate_request"] and state.get("group_validated"):
            # Group placement — find apartment with enough empty rooms
            group_size = len(state["roommate_ids"]) + 1  # include current student

            # Find apartments with enough empty rent-ready rooms
            from sqlalchemy import func
            apartments = (
                db.query(
                    Room.building,
                    Room.apartment_number,
                    Room.room_type,
                    func.count(Room.id).label("empty_rooms")
                )
                .filter(
                    Room.is_occupied == False,
                    Room.is_rent_ready == True
                )
                .group_by(Room.building, Room.apartment_number, Room.room_type)
                .having(func.count(Room.id) >= group_size)
                .all()
            )

            available = []
            for apt in apartments:
                rooms = db.query(Room).filter(
                    Room.building == apt.building,
                    Room.apartment_number == apt.apartment_number,
                    Room.is_occupied == False,
                    Room.is_rent_ready == True
                ).limit(group_size).all()

                available.append({
                    "type": "group",
                    "building": apt.building,
                    "apartment_number": apt.apartment_number,
                    "rooms": [{"id": r.id, "room_number": r.room_number} for r in rooms]
                })

            state["available_rooms"] = available

        else:
            # Individual placement
            # Step 1 — partial rooms first
            partial_rooms = (
                db.query(Room)
                .filter(
                    Room.is_occupied == False,
                    Room.is_rent_ready == True
                )
                .join(
                    Allocation,
                    (Allocation.room_id == Room.id) &
                    (Allocation.status == AllocationStatus.allocated),
                    isouter=True
                )
                .all()
            )

            # Filter to rooms in apartments that have existing residents
            partial = []
            empty   = []

            for room in partial_rooms:
                # Check if apartment has any occupied rooms
                occupied_in_apt = db.query(Room).filter(
                    Room.building         == room.building,
                    Room.apartment_number == room.apartment_number,
                    Room.is_occupied      == True
                ).count()

                room_dict = {
                    "type":             "individual",
                    "id":               room.id,
                    "room_number":      room.room_number,
                    "building":         room.building,
                    "apartment_number": room.apartment_number,
                    "room_type":        room.room_type.value,
                    "has_roommates":    occupied_in_apt > 0
                }

                if occupied_in_apt > 0:
                    partial.append(room_dict)
                else:
                    empty.append(room_dict)

            # Partial rooms first then empty
            state["available_rooms"] = partial + empty

        print(f"🔍 Found {len(state['available_rooms'])} available options")
        return state

    finally:
        db.close()


# ─────────────────────────────────────────────
# NODE 4 — Score Compatibility
# Calculates compatibility score between student
# and existing apartment residents
# ─────────────────────────────────────────────
def score_compatibility_node(state: HousingAgentState) -> HousingAgentState:
    db = SessionLocal()
    try:
        state["current_node"] = "score_compatibility"

        if not state["available_rooms"]:
            state["compatibility_score"] = None
            return state

        # Get first available room option
        best_room   = None
        best_score  = 0.0

        student_profile = state["student_profile"]

        for room_option in state["available_rooms"]:
            if not room_option.get("has_roommates", False):
                # Empty room — no compatibility needed, score is 1.0
                best_room  = room_option
                best_score = 1.0
                break

            # Get existing residents in this apartment
            existing_residents = (
                db.query(Student)
                .join(Allocation, Allocation.student_id == Student.id)
                .join(Room, Allocation.room_id == Room.id)
                .filter(
                    Room.building         == room_option["building"],
                    Room.apartment_number == room_option["apartment_number"],
                    Room.is_occupied      == True,
                    Allocation.status     == AllocationStatus.allocated
                )
                .all()
            )

            if not existing_residents:
                best_room  = room_option
                best_score = 1.0
                break

            # Calculate compatibility score
            scores = []
            for resident in existing_residents:
                pref = db.query(StudentPreference).filter(
                    StudentPreference.student_id == resident.id
                ).first()

                if not pref:
                    continue

                score = 0.0
                weights = {
                    "sleep_schedule":  0.35,
                    "noise_tolerance": 0.25,
                    "cleanliness":     0.25,
                    "study_habits":    0.15
                }

                # Sleep schedule match
                if student_profile.get("sleep_schedule") == pref.sleep_schedule.value:
                    score += weights["sleep_schedule"]

                # Noise tolerance — within 1 point
                noise_diff = abs(
                    (student_profile.get("noise_tolerance") or 3) - pref.noise_tolerance
                )
                score += weights["noise_tolerance"] * max(0, (5 - noise_diff) / 5)

                # Cleanliness — within 1 point
                clean_diff = abs(
                    (student_profile.get("cleanliness") or 3) - pref.cleanliness
                )
                score += weights["cleanliness"] * max(0, (5 - clean_diff) / 5)

                # Study habits match
                if student_profile.get("study_habits") == pref.study_habits.value:
                    score += weights["study_habits"]

                scores.append(score)

            avg_score = sum(scores) / len(scores) if scores else 0.0

            if avg_score > best_score:
                best_score = avg_score
                best_room  = room_option

        state["room_id"]             = best_room["id"] if best_room and "id" in best_room else None
        state["compatibility_score"] = round(best_score, 2)

        print(f"📊 Best compatibility score: {state['compatibility_score']}")
        return state

    finally:
        db.close()
# ─────────────────────────────────────────────
# NODE 5 — Assign Room
# Assigns student to room if score meets threshold
# ─────────────────────────────────────────────
def assign_room_node(state: HousingAgentState) -> HousingAgentState:
    db = SessionLocal()
    try:
        state["current_node"] = "assign_room"
        COMPATIBILITY_THRESHOLD = 0.65

        # Check score threshold
        if (state["compatibility_score"] is not None and
                state["compatibility_score"] < COMPATIBILITY_THRESHOLD and
                state["available_rooms"] and
                state["available_rooms"][0].get("has_roommates")):
            state["attempts"] += 1
            state["status"]    = "retry"
            state["error_reason"] = f"Compatibility score {state['compatibility_score']} below threshold"
            print(f"⚠️  Score too low — attempt {state['attempts']}")
            return state

        if not state["room_id"]:
            state["attempts"] += 1
            state["status"]    = "retry"
            state["error_reason"] = "No suitable room found"
            return state

        # Assign student to room
        room = db.query(Room).filter(Room.id == state["room_id"]).first()

        if not room or not room.is_rent_ready or room.is_occupied:
            state["attempts"] += 1
            state["status"]    = "retry"
            state["error_reason"] = f"Room {state['room_id']} not available"
            return state

        # Create allocation record
        allocation = Allocation(
            student_id          = state["student_id"],
            room_id             = state["room_id"],
            request_id          = state["request_id"],
            status              = AllocationStatus.allocated,
            compatibility_score = state["compatibility_score"],
            is_reallocated      = state["attempts"] > 0,
            allocated_at        = datetime.utcnow()
        )
        db.add(allocation)

        # Update room
        room.is_occupied = True

        # Update student
        student = db.query(Student).filter(
            Student.id == state["student_id"]
        ).first()
        student.is_allocated = True

        # Update request
        request = db.query(Request).filter(
            Request.id == state["request_id"]
        ).first()
        request.status       = RequestStatus.completed
        request.processed_at = datetime.utcnow()

        db.commit()

        state["status"] = "allocated"
        print(f"✅ Student {state['student_id']} assigned to room {room.room_number}")
        return state

    finally:
        db.close()


# ─────────────────────────────────────────────
# NODE 6 — Handle Unresolved
# Flags student for human review after max attempts
# ─────────────────────────────────────────────
def handle_unresolved_node(state: HousingAgentState) -> HousingAgentState:
    db = SessionLocal()
    try:
        state["current_node"] = "handle_unresolved"

        # Update request status
        request = db.query(Request).filter(
            Request.id == state["request_id"]
        ).first()
        request.status        = RequestStatus.rejected
        request.outcome_notes = state.get("error_reason", "Max attempts reached")
        request.processed_at  = datetime.utcnow()

        db.commit()

        state["status"] = "unresolved"
        print(f"🚨 Student {state['student_id']} flagged as unresolved")
        return state

    finally:
        db.close()


# ─────────────────────────────────────────────
# NODE 7 — Handle On Hold
# Puts request on hold — too early or incomplete group
# ─────────────────────────────────────────────
def handle_on_hold_node(state: HousingAgentState) -> HousingAgentState:
    db = SessionLocal()
    try:
        state["current_node"] = "handle_on_hold"

        request = db.query(Request).filter(
            Request.id == state["request_id"]
        ).first()
        request.status        = RequestStatus.on_hold
        request.outcome_notes = state.get("error_reason")

        db.commit()

        state["status"] = "on_hold"
        print(f"⏸️  Request {state['request_id']} put on hold: {state.get('error_reason')}")
        return state

    finally:
        db.close()


# ─────────────────────────────────────────────
# NODE 8 — Send Notification
# Sends appropriate email based on outcome
# ─────────────────────────────────────────────
def send_notification_node(state: HousingAgentState) -> HousingAgentState:
    db = SessionLocal()
    try:
        state["current_node"] = "send_notification"

        # Determine notification type and message
        status = state["status"]

        if status == "allocated":
            notif_type = NotificationType.allocated
            message    = (
                f"Congratulations! You have been allocated to room. "
                f"Compatibility score: {state.get('compatibility_score', 'N/A')}"
            )
        elif status == "unresolved":
            notif_type = NotificationType.unresolved
            message    = (
                "We were unable to find a suitable room for you at this time. "
                "A housing officer will contact you shortly."
            )
        elif status == "on_hold" and state.get("error_reason", "").startswith("Only"):
            notif_type = NotificationType.too_early
            message    = (
                f"Your room change request was received but it is too early to process. "
                f"{state.get('error_reason')}. We will process it after 3 days."
            )
        elif status == "on_hold" and "roommates" in state.get("error_reason", ""):
            notif_type = NotificationType.waiting_for_group
            message    = (
                "Your request is on hold. We are waiting for all your requested "
                "roommates to submit their applications."
            )
        else:
            notif_type = NotificationType.unresolved
            message    = "Your request could not be processed at this time."

        # Save notification
        notification = Notification(
            student_id    = state["student_id"],
            request_id    = state["request_id"],
            type          = notif_type,
            message       = message,
            is_email_sent = EmailStatus.sent,
            sent_at       = datetime.utcnow()
        )
        db.add(notification)
        db.commit()

        state["notifications_sent"].append(notif_type.value)
        print(f"📧 Notification sent: {notif_type.value}")
        return state

    finally:
        db.close()