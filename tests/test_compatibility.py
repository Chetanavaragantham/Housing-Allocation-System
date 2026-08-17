import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


def calculate_compatibility(student_profile: dict, resident_profile: dict) -> float:
    """
    Calculate compatibility score between two students.
    Returns a float between 0.0 and 1.0
    """
    weights = {
        "sleep_schedule":  0.35,
        "noise_tolerance": 0.25,
        "cleanliness":     0.25,
        "study_habits":    0.15
    }

    score = 0.0

    # Sleep schedule
    if student_profile.get("sleep_schedule") == resident_profile.get("sleep_schedule"):
        score += weights["sleep_schedule"]

    # Noise tolerance
    noise_diff = abs(
        (student_profile.get("noise_tolerance") or 3) -
        (resident_profile.get("noise_tolerance") or 3)
    )
    score += weights["noise_tolerance"] * max(0, (5 - noise_diff) / 5)

    # Cleanliness
    clean_diff = abs(
        (student_profile.get("cleanliness") or 3) -
        (resident_profile.get("cleanliness") or 3)
    )
    score += weights["cleanliness"] * max(0, (5 - clean_diff) / 5)

    # Study habits
    if student_profile.get("study_habits") == resident_profile.get("study_habits"):
        score += weights["study_habits"]

    return round(score, 2)


# ─────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────

def test_perfect_compatibility():
    """Two identical profiles should score 1.0"""
    profile = {
        "sleep_schedule":  "early_bird",
        "noise_tolerance": 3,
        "cleanliness":     3,
        "study_habits":    "quiet"
    }
    score = calculate_compatibility(profile, profile)
    assert score == 1.0


def test_zero_compatibility():
    """Completely opposite profiles should score very low"""
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
    assert score < 0.5


def test_partial_compatibility():
    """Same sleep and study habits but different noise/cleanliness"""
    student = {
        "sleep_schedule":  "early_bird",
        "noise_tolerance": 2,
        "cleanliness":     2,
        "study_habits":    "quiet"
    }
    resident = {
        "sleep_schedule":  "early_bird",
        "noise_tolerance": 4,
        "cleanliness":     4,
        "study_habits":    "quiet"
    }
    score = calculate_compatibility(student, resident)
    assert 0.5 < score < 1.0


def test_score_is_between_0_and_1():
    """Score must always be between 0.0 and 1.0"""
    student = {
        "sleep_schedule":  "early_bird",
        "noise_tolerance": 3,
        "cleanliness":     3,
        "study_habits":    "quiet"
    }
    resident = {
        "sleep_schedule":  "night_owl",
        "noise_tolerance": 3,
        "cleanliness":     3,
        "study_habits":    "group"
    }
    score = calculate_compatibility(student, resident)
    assert 0.0 <= score <= 1.0


def test_threshold_above_065():
    """Compatible students should score above 0.65 threshold"""
    student = {
        "sleep_schedule":  "early_bird",
        "noise_tolerance": 2,
        "cleanliness":     3,
        "study_habits":    "quiet"
    }
    resident = {
        "sleep_schedule":  "early_bird",
        "noise_tolerance": 3,
        "cleanliness":     3,
        "study_habits":    "quiet"
    }
    score = calculate_compatibility(student, resident)
    assert score >= 0.65


def test_missing_fields_dont_crash():
    """Missing fields should not cause errors"""
    student  = {"sleep_schedule": "early_bird"}
    resident = {"noise_tolerance": 3}
    score = calculate_compatibility(student, resident)
    assert isinstance(score, float)