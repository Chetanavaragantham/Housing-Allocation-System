from typing import TypedDict, Optional, List


class HousingAgentState(TypedDict):
    # Request info
    request_id:       int
    request_type:     str        # application or room_change
    student_id:       int
    student_profile:  dict       # full student + preference data

    # Roommate info
    has_roommate_request: bool
    roommate_ids:         List[int]
    group_validated:      bool   # have all roommates submitted?

    # Room info
    available_rooms:     List[dict]
    room_id:             Optional[int]
    compatibility_score: Optional[float]

    # Process tracking
    attempts:     int
    current_node: str
    status:       str   # processing, allocated, on_hold, unresolved, rejected
    error_reason: Optional[str]

    # Notifications
    notifications_sent: List[str]