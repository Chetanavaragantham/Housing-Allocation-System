import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ─────────────────────────────────────────────
# HEALTH CHECK TESTS
# ─────────────────────────────────────────────

def test_health_check():
    """API should return healthy status"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    """Root endpoint should return system info"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Housing Allocation System" in response.json()["message"]


# ─────────────────────────────────────────────
# AUTH TESTS
# ─────────────────────────────────────────────

def test_register_student(client, setup_test_db):
    """Should successfully register a new student"""
    response = client.post("/api/v1/auth/register", json={
        "student_id":  "PYTEST001",
        "first_name":  "Pytest",
        "last_name":   "Student",
        "email":       "pytest@university.edu",
        "password":    "testpass123",
        "gender":      "female"
    })
    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["data"]["student_id"] == "PYTEST001"


def test_register_duplicate_email(client, setup_test_db):
    """Should reject duplicate email registration"""
    # Register first time
    client.post("/api/v1/auth/register", json={
        "student_id": "PYTEST002",
        "first_name": "Pytest",
        "last_name":  "Two",
        "email":      "duplicate@university.edu",
        "password":   "testpass123"
    })

    # Register again with same email
    response = client.post("/api/v1/auth/register", json={
        "student_id": "PYTEST003",
        "first_name": "Pytest",
        "last_name":  "Three",
        "email":      "duplicate@university.edu",
        "password":   "testpass123"
    })
    assert response.status_code == 409


def test_login_valid_credentials(client, setup_test_db):
    """Should return token on valid login"""
    # Register first
    client.post("/api/v1/auth/register", json={
        "student_id": "PYTEST004",
        "first_name": "Login",
        "last_name":  "Test",
        "email":      "login@university.edu",
        "password":   "testpass123"
    })

    # Login
    response = client.post("/api/v1/auth/login", json={
        "email":    "login@university.edu",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_invalid_credentials(client, setup_test_db):
    """Should reject invalid credentials"""
    response = client.post("/api/v1/auth/login", json={
        "email":    "wrong@university.edu",
        "password": "wrongpass"
    })
    assert response.status_code == 401


# ─────────────────────────────────────────────
# REQUEST TESTS
# ─────────────────────────────────────────────

def test_get_all_requests(client, setup_test_db):
    """Should return list of requests"""
    response = client.get("/api/v1/requests/")
    assert response.status_code == 200
    assert "data" in response.json()
    assert "total" in response.json()


def test_get_all_allocations(client, setup_test_db):
    """Should return list of allocations"""
    response = client.get("/api/v1/allocations/")
    assert response.status_code == 200
    assert "data" in response.json()


def test_get_unresolved(client, setup_test_db):
    """Should return unresolved allocations"""
    response = client.get("/api/v1/allocations/unresolved")
    assert response.status_code == 200
    assert "data" in response.json()


def test_get_metrics(client, setup_test_db):
    """Should return agent metrics"""
    response = client.get("/api/v1/agent/metrics")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "total_students" in data
    assert "allocation_rate" in data
    assert "unresolved_count" in data


def test_cancel_nonexistent_request(client, setup_test_db):
    """Should return 404 for nonexistent request"""
    response = client.patch("/api/v1/requests/99999/cancel")
    assert response.status_code == 404


def test_delete_nonexistent_request(client, setup_test_db):
    """Should return 404 for nonexistent request"""
    response = client.delete("/api/v1/requests/99999")
    assert response.status_code == 404