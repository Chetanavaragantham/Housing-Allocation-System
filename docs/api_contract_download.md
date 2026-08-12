# API Contract Specification
**Project:** Housing Allocation System
**Version:** v1.0
**Base URL:** `http://localhost:8000/api/v1`
**Date:** 2026-06-08
**Status:** Draft

---

## Overview

This document defines every API endpoint in the Housing Allocation System.
It serves as the contract between the frontend, backend, and agent layers.

### Authentication
All endpoints except `/auth/register` and `/auth/login` require a Bearer token
in the Authorization header:
```
Authorization: Bearer <token>
```

### Standard Error Response
All errors follow this format:
```json
{
  "status": "error",
  "code": 400,
  "message": "Description of what went wrong"
}
```

### HTTP Status Codes Used
| Code | Meaning |
|------|---------|
| 200 | Success — data returned |
| 201 | Created — new record created |
| 400 | Bad Request — invalid input |
| 401 | Unauthorized — not logged in |
| 403 | Forbidden — not allowed |
| 404 | Not Found — record doesn't exist |
| 409 | Conflict — duplicate or rule violation |
| 422 | Unprocessable — validation failed |
| 500 | Server Error — something broke |

---

## AUTH ENDPOINTS

---

### POST /auth/register
Register a new student account.

**Access:** Public

**Request Body:**
```json
{
  "student_id": "STU001",
  "first_name": "Chetana",
  "last_name": "Varagantham",
  "email": "chetana@university.edu",
  "password": "securepassword123",
  "phone_number": "555-0101",
  "date_of_birth": "2002-05-15",
  "gender": "female",
  "intake_date": "2026-09-01"
}
```

**Response 201:**
```json
{
  "status": "success",
  "message": "Account created successfully",
  "data": {
    "id": 1,
    "student_id": "STU001",
    "email": "chetana@university.edu",
    "is_allocated": false,
    "created_at": "2026-06-08T10:00:00Z"
  }
}
```

**Errors:** 409 if email or student_id already exists

---

### POST /auth/login
Login and receive access token.

**Access:** Public

**Request Body:**
```json
{
  "email": "chetana@university.edu",
  "password": "securepassword123"
}
```

**Response 200:**
```json
{
  "status": "success",
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "role": "student"
}
```

**Errors:** 401 if credentials are wrong

---

### POST /auth/logout
Invalidate the current session token.

**Access:** Student, Staff

**Response 200:**
```json
{
  "status": "success",
  "message": "Logged out successfully"
}
```

---

## STUDENT ENDPOINTS

---

### POST /requests
Submit a new housing application or room change request.

**Access:** Student only

**Request Body:**
```json
{
  "request_type": "application",
  "requested_roommate_1": "STU002",
  "requested_roommate_2": null,
  "requested_roommate_3": null
}
```

**Response 201:**
```json
{
  "status": "success",
  "message": "Application submitted successfully",
  "data": {
    "id": 45,
    "request_type": "application",
    "status": "pending",
    "submitted_at": "2026-06-08T10:30:00Z"
  }
}
```

**Errors:**
- 409 if student already has a pending application
- 409 if room_change request submitted within 3 days of allocation
- 422 if request_type is invalid

---

### PATCH /requests/{request_id}
Edit an application before it has been submitted for processing.

**Access:** Student only (own requests)

**Request Body:** (only send fields you want to change)
```json
{
  "requested_roommate_1": "STU003",
  "requested_roommate_2": "STU004"
}
```

**Response 200:**
```json
{
  "status": "success",
  "message": "Request updated successfully",
  "data": {
    "id": 45,
    "requested_roommate_1": "STU003",
    "requested_roommate_2": "STU004",
    "updated_at": "2026-06-08T11:00:00Z"
  }
}
```

**Errors:**
- 403 if request belongs to another student
- 409 if request has already been processed
- 404 if request_id not found

---

### PATCH /requests/{request_id}/cancel
Cancel a submitted application.

**Access:** Student only (own requests)

**Request Body:** None required

**Response 200:**
```json
{
  "status": "success",
  "message": "Request cancelled successfully",
  "data": {
    "id": 45,
    "status": "cancelled",
    "updated_at": "2026-06-08T11:30:00Z"
  }
}
```

**Errors:**
- 403 if request belongs to another student
- 409 if request is already processed — cannot cancel
- 404 if request_id not found

---

### GET /allocations/me
View the current student's allocation status.

**Access:** Student only

**Response 200:**
```json
{
  "status": "success",
  "data": {
    "allocation_id": 12,
    "status": "allocated",
    "room": {
      "room_number": "101A",
      "building": "A",
      "apartment_number": "101",
      "room_type": "double"
    },
    "compatibility_score": 0.82,
    "allocated_at": "2026-06-08T12:00:00Z"
  }
}
```

**Response 200 (not yet allocated):**
```json
{
  "status": "success",
  "data": null,
  "message": "No allocation found. Your application is pending."
}
```

---

### GET /requests/me
View the current student's request history.

**Access:** Student only

**Response 200:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 45,
      "request_type": "application",
      "status": "completed",
      "submitted_at": "2026-06-08T10:30:00Z",
      "processed_at": "2026-06-08T12:00:00Z"
    }
  ]
}
```

---

## STAFF ENDPOINTS

---

### GET /requests
View all student submissions. Supports filtering and pagination.

**Access:** Staff only

**Query Parameters:**
```
status       → filter by status: pending, processing, completed, rejected
request_type → filter by type: application, room_change
page         → page number (default: 1)
limit        → results per page (default: 20)
```

**Example:** `GET /api/v1/requests?status=pending&page=1&limit=20`

**Response 200:**
```json
{
  "status": "success",
  "total": 150,
  "page": 1,
  "limit": 20,
  "data": [
    {
      "id": 45,
      "student_id": "STU001",
      "student_name": "Chetana Varagantham",
      "request_type": "application",
      "status": "pending",
      "submitted_at": "2026-06-08T10:30:00Z"
    }
  ]
}
```

---

### PATCH /requests/{request_id}/staff
Staff manually edits any submission.

**Access:** Staff only

**Request Body:**
```json
{
  "status": "pending",
  "requested_roommate_1": "STU005"
}
```

**Response 200:**
```json
{
  "status": "success",
  "message": "Request updated by staff",
  "data": {
    "id": 45,
    "updated_at": "2026-06-08T13:00:00Z"
  }
}
```

---

### DELETE /requests/{request_id}
Hard delete a submission. Irreversible.

**Access:** Staff only

**Response 200:**
```json
{
  "status": "success",
  "message": "Request deleted successfully"
}
```

**Errors:** 404 if request_id not found

---

### GET /allocations
View all allocations across all students.

**Access:** Staff only

**Query Parameters:**
```
status    → filter by: pending, allocated, reallocated, unresolved
building  → filter by: A, B, C
page      → page number
limit     → results per page
```

**Response 200:**
```json
{
  "status": "success",
  "total": 200,
  "data": [
    {
      "allocation_id": 12,
      "student_id": "STU001",
      "student_name": "Chetana Varagantham",
      "room_number": "101A",
      "building": "A",
      "status": "allocated",
      "compatibility_score": 0.82,
      "allocated_at": "2026-06-08T12:00:00Z"
    }
  ]
}
```

---

### GET /allocations/unresolved
View all students the agent could not place after 3 attempts.

**Access:** Staff only

**Response 200:**
```json
{
  "status": "success",
  "total": 3,
  "data": [
    {
      "allocation_id": 18,
      "student_id": "STU009",
      "student_name": "John Smith",
      "status": "unresolved",
      "attempts": 3,
      "last_failure_reason": "No compatible rooms available",
      "allocated_at": null
    }
  ]
}
```

---

### PATCH /allocations/{allocation_id}/manual
Staff manually assigns an unresolved student to a specific room.

**Access:** Staff only

**Request Body:**
```json
{
  "room_id": 42,
  "override_reason": "Manual placement by housing officer"
}
```

**Response 200:**
```json
{
  "status": "success",
  "message": "Student manually assigned to room 101A",
  "data": {
    "allocation_id": 18,
    "room_number": "101A",
    "building": "A",
    "status": "allocated",
    "is_reallocated": true
  }
}
```

---

## AGENT ENDPOINTS

---

### POST /agent/run
Trigger the agent to process all pending requests in the queue.

**Access:** Staff only

**Request Body:**
```json
{
  "mode": "full"
}
```

**Response 200:**
```json
{
  "status": "success",
  "message": "Agent run started",
  "data": {
    "run_id": "run_abc123",
    "requests_queued": 47,
    "started_at": "2026-06-08T14:00:00Z"
  }
}
```

---

### GET /agent/run/{run_id}
Check the status of an agent run.

**Access:** Staff only

**Response 200:**
```json
{
  "status": "success",
  "data": {
    "run_id": "run_abc123",
    "status": "completed",
    "requests_processed": 47,
    "successfully_allocated": 44,
    "unresolved": 3,
    "started_at": "2026-06-08T14:00:00Z",
    "completed_at": "2026-06-08T14:03:22Z"
  }
}
```

---

### GET /agent/metrics
View allocation performance metrics.

**Access:** Staff only

**Response 200:**
```json
{
  "status": "success",
  "data": {
    "total_students": 200,
    "successfully_allocated": 188,
    "allocation_rate": 0.94,
    "average_compatibility_score": 0.76,
    "total_reallocations": 12,
    "reallocation_rate": 0.06,
    "unresolved_count": 3,
    "unresolved_rate": 0.015
  }
}
```

---

## ENDPOINT SUMMARY

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | /auth/register | Public | Register student |
| POST | /auth/login | Public | Login |
| POST | /auth/logout | Auth | Logout |
| POST | /requests | Student | Submit application |
| PATCH | /requests/{id} | Student | Edit application |
| PATCH | /requests/{id}/cancel | Student | Cancel application |
| GET | /requests/me | Student | View own requests |
| GET | /allocations/me | Student | View own allocation |
| GET | /requests | Staff | View all submissions |
| PATCH | /requests/{id}/staff | Staff | Edit any submission |
| DELETE | /requests/{id} | Staff | Delete submission |
| GET | /allocations | Staff | View all allocations |
| GET | /allocations/unresolved | Staff | View unresolved cases |
| PATCH | /allocations/{id}/manual | Staff | Manual room assignment |
| POST | /agent/run | Staff | Trigger agent |
| GET | /agent/run/{run_id} | Staff | Check agent run status |
| GET | /agent/metrics | Staff | View metrics |
