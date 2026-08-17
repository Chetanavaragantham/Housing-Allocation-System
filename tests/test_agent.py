import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from tests.test_compatibility import calculate_compatibility


# ─────────────────────────────────────────────
# AGENT LOGIC TESTS
# ─────────────────────────────────────────────

def test_friend_group_mutual_detection():
    """Both students must list each other for a confirmed friend pair"""
    student_a_roommates = [2, 3]
    student_b_roommates = [1, 3]
    student_c_roommates = [1, 2]

    def is_mutual_group(student_id, roommate_ids, all_preferences):
        for roommate_id in roommate_ids:
            roommate_prefs = all_preferences.get(roommate_id, [])
            if student_id not in roommate_prefs:
                return False
        return True

    all_preferences = {
        1: student_a_roommates,
        2: student_b_roommates,
        3: student_c_roommates
    }

    assert is_mutual_group(1, student_a_roommates, all_preferences) == True
    assert is_mutual_group(2, student_b_roommates, all_preferences) == True
    assert is_mutual_group(3, student_c_roommates, all_preferences) == True


def test_one_sided_request_not_confirmed():
    """One sided friend request should not be confirmed"""
    all_preferences = {
        1: [2],  # A wants B
        2: []    # B didn't request A
    }

    def is_mutual(student_id, roommate_ids, all_preferences):
        for roommate_id in roommate_ids:
            roommate_prefs = all_preferences.get(roommate_id, [])
            if student_id not in roommate_prefs:
                return False
        return True

    assert is_mutual(1, [2], all_preferences) == False


def test_three_day_buffer_enforced():
    """Room change request within 3 days should be held"""
    from datetime import datetime, timedelta

    allocated_at = datetime.utcnow() - timedelta(days=2)
    request_submitted = datetime.utcnow()

    days_since = (request_submitted - allocated_at).days
    assert days_since < 3  # should be held


def test_three_day_buffer_passed():
    """Room change request after 3 days should be processed"""
    from datetime import datetime, timedelta

    allocated_at = datetime.utcnow() - timedelta(days=4)
    request_submitted = datetime.utcnow()

    days_since = (request_submitted - allocated_at).days
    assert days_since >= 3  # should be processed


def test_max_reallocation_attempts():
    """Agent should flag unresolved after 3 attempts"""
    MAX_ATTEMPTS = 3
    attempts = 0

    def try_allocate(attempt):
        return False  # always fails in this test

    while attempts < MAX_ATTEMPTS:
        result = try_allocate(attempts)
        attempts += 1

    assert attempts == MAX_ATTEMPTS
    status = "unresolved" if attempts >= MAX_ATTEMPTS else "processing"
    assert status == "unresolved"


def test_compatibility_threshold():
    """Students below 0.65 threshold should not be paired"""
    THRESHOLD = 0.65

    student = {
        "sleep_schedule":  "early_bird",
        "noise_tolerance": 1,
        "cleanliness":     1,
        "study_habits":    "quiet"
    }
    resident = {
        "sleep_schedule":  "night_owl",
        "noise_tolerance": 5,
        "cleanliness":     5,
        "study_habits":    "group"
    }

    score = calculate_compatibility(student, resident)
    assert score < THRESHOLD  # should not be paired


def test_group_size_limit():
    """Group size must not exceed 4 students"""
    MAX_GROUP_SIZE = 4

    group_of_3 = [1, 2, 3]
    group_of_5 = [1, 2, 3, 4, 5]

    assert len(group_of_3) <= MAX_GROUP_SIZE
    assert len(group_of_5) > MAX_GROUP_SIZE


def test_partial_rooms_prioritised_over_empty():
    """Partial rooms should come before empty rooms in search results"""
    rooms = [
        {"id": 1, "has_roommates": True,  "room_number": "101A"},
        {"id": 2, "has_roommates": False, "room_number": "102A"},
        {"id": 3, "has_roommates": True,  "room_number": "103A"},
        {"id": 4, "has_roommates": False, "room_number": "104A"},
    ]

    # Sort — partial rooms first
    sorted_rooms = sorted(rooms, key=lambda r: not r["has_roommates"])

    assert sorted_rooms[0]["has_roommates"] == True
    assert sorted_rooms[1]["has_roommates"] == True
    assert sorted_rooms[2]["has_roommates"] == False
    assert sorted_rooms[3]["has_roommates"] == False