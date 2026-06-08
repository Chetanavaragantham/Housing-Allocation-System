# Data Dictionary
**Project:** Housing Allocation System  
**Version:** 1.0  
**Date:** 2026-06-08  
**Status:** Final

---

## Overview

This document formally defines every table, column, data type, constraint, and business rule in the Housing Allocation System database. It is the single source of truth for all data definitions.

---

## Table 1 — students

Stores the core profile of every student applying for housing.

| Column | Type | Nullable | Unique | Default | Description |
|--------|------|----------|--------|---------|-------------|
| id | integer | NO | YES | auto-increment | Internal primary key |
| student_id | varchar | NO | YES | — | University-issued student number e.g. "STU001" |
| first_name | varchar | NO | NO | — | Student's first name |
| last_name | varchar | NO | NO | — | Student's last name |
| email | varchar | NO | YES | — | University email address |
| phone_number | varchar | YES | NO | — | Contact phone number |
| date_of_birth | date | YES | NO | — | Student's date of birth |
| gender | enum | YES | NO | — | Values: male, female, other |
| intake_date | date | YES | NO | — | Date student joined the university |
| is_allocated | boolean | NO | NO | false | Whether student has been assigned a room |
| created_at | timestamp | NO | NO | now() | Record creation timestamp |
| updated_at | timestamp | YES | NO | — | Last modification timestamp |

**Indexes:** student_id, email  
**Business Rules:**
- student_id and email must be unique across all records
- is_allocated is set to true by the agent only after a successful room assignment

---

## Table 2 — student_preferences

Stores lifestyle preferences and roommate requests for each student. Used by the agent to calculate compatibility scores.

| Column | Type | Nullable | Unique | Default | Description |
|--------|------|----------|--------|---------|-------------|
| id | integer | NO | YES | auto-increment | Internal primary key |
| student_id | integer | NO | YES | — | FK → students.id |
| requested_roommate_1 | integer | YES | NO | — | FK → students.id. First preferred roommate |
| requested_roommate_2 | integer | YES | NO | — | FK → students.id. Second preferred roommate |
| requested_roommate_3 | integer | YES | NO | — | FK → students.id. Third preferred roommate |
| sleep_schedule | enum | NO | NO | — | Values: early_bird, night_owl |
| noise_tolerance | integer | NO | NO | — | Scale 1–5. 1=very quiet, 5=very tolerant |
| cleanliness | integer | NO | NO | — | Scale 1–5. 1=very clean, 5=relaxed |
| study_habits | enum | NO | NO | — | Values: quiet, group |
| diet | enum | YES | NO | — | Values: vegetarian, non_vegetarian, vegan |
| created_at | timestamp | NO | NO | now() | Record creation timestamp |
| updated_at | timestamp | YES | NO | — | Last modification timestamp |

**Indexes:** student_id  
**Business Rules:**
- One preference record per student (1:1 with students)
- requested_roommate columns are self-referential FKs pointing back to students.id
- A friend group is confirmed only when all members list each other mutually
- Maximum 3 roommate requests — reflects maximum apartment size of 4 students
- noise_tolerance and cleanliness values must be between 1 and 5

---

## Table 3 — rooms

Stores every individual room in the housing inventory. One row = one physical room.

| Column | Type | Nullable | Unique | Default | Description |
|--------|------|----------|--------|---------|-------------|
| id | integer | NO | YES | auto-increment | Internal primary key |
| room_number | varchar | NO | NO | — | Room identifier e.g. "101A" |
| building | enum | NO | NO | — | Values: A, B, C |
| apartment_number | varchar | NO | NO | — | Apartment this room belongs to e.g. "101" |
| room_type | enum | NO | NO | — | Values: private, double, triple, quad |
| is_occupied | boolean | NO | NO | false | Whether a student currently lives in this room |
| is_rent_ready | boolean | NO | NO | false | Whether room has passed inspection |
| room_issues | text | YES | NO | — | Description of outstanding issues if not rent ready |
| maintenance_status | enum | NO | NO | not_applicable | Current maintenance workflow status |
| created_at | timestamp | NO | NO | now() | Record creation timestamp |
| updated_at | timestamp | YES | NO | — | Last modification timestamp |

**Composite Unique Constraint:** (building, room_number) — no two rooms in the same building can share a room number  
**Indexes:** building, room_number, apartment_number, is_occupied, is_rent_ready

**Enum Values — room_type:**
- private — 1 room in apartment, fully private
- double — 2 rooms share common areas
- triple — 3 rooms share common areas
- quad — 4 rooms share common areas

**Enum Values — maintenance_status:**
- not_applicable — room has no issues
- pending_escalation — issue identified, not yet reported
- escalated — issue reported to maintenance team
- work_assigned — maintenance team has accepted the job
- work_in_progress — actively being fixed
- completed — work done, awaiting re-inspection
- rent_ready — re-inspected and approved

**Business Rules:**
- Each room holds exactly 1 student (one student per physical room)
- Friend groups share an apartment — not a room
- is_available is a computed property: not is_occupied
- Agent only assigns students to rooms where is_rent_ready = true AND is_occupied = false
- room_type describes the apartment configuration, not the individual room

---

## Table 4 — allocations

Records every room assignment made by the agent. Each row is one student-to-room assignment event.

| Column | Type | Nullable | Unique | Default | Description |
|--------|------|----------|--------|---------|-------------|
| id | integer | NO | YES | auto-increment | Internal primary key |
| student_id | integer | NO | NO | — | FK → students.id |
| room_id | integer | NO | NO | — | FK → rooms.id |
| request_id | integer | NO | NO | — | FK → requests.id. The request that triggered this allocation |
| status | enum | NO | NO | pending | Current allocation status |
| compatibility_score | float | YES | NO | — | Score calculated by agent (0.0–1.0). Null for friend group placements |
| is_reallocated | boolean | NO | NO | false | Whether this is a reallocation after a previous failure |
| allocated_at | timestamp | NO | NO | now() | When the agent made this assignment |
| created_at | timestamp | NO | NO | now() | Record creation timestamp |
| updated_at | timestamp | YES | NO | — | Last modification timestamp |

**Indexes:** student_id, room_id, request_id, status

**Enum Values — status:**
- pending — agent is processing
- allocated — successfully assigned
- reallocated — moved after initial assignment
- unresolved — agent could not find a suitable room after max attempts

**Business Rules:**
- request_id creates a full audit trail — every allocation is traceable to the request that triggered it
- compatibility_score is null for friend group placements — friends are placed together regardless of score
- When is_reallocated = true, the previous allocation record remains in the table with status = reallocated
- Room change requests after initial allocation require a minimum 3 day gap — enforced by comparing requests.submitted_at with the original allocations.allocated_at

---

## Table 5 — requests

Stores every housing application and room change request submitted by students. The agent processes requests from this table in submission order (first come first serve).

| Column | Type | Nullable | Unique | Default | Description |
|--------|------|----------|--------|---------|-------------|
| id | integer | NO | YES | auto-increment | Internal primary key |
| student_id | integer | NO | NO | — | FK → students.id. Who submitted this request |
| requested_roommate_1 | integer | YES | NO | — | FK → students.id. First requested roommate |
| requested_roommate_2 | integer | YES | NO | — | FK → students.id. Second requested roommate |
| requested_roommate_3 | integer | YES | NO | — | FK → students.id. Third requested roommate |
| request_type | enum | NO | NO | — | Values: application, room_change |
| status | enum | NO | NO | pending | Current processing status |
| rejection_reason | text | YES | NO | — | Why request was rejected if applicable |
| outcome_notes | text | YES | NO | — | Agent's decision notes |
| submitted_at | timestamp | NO | NO | now() | When student submitted the request |
| processed_at | timestamp | YES | NO | — | When agent finished processing |
| created_at | timestamp | NO | NO | now() | Record creation timestamp |
| updated_at | timestamp | YES | NO | — | Last modification timestamp |

**Indexes:** student_id, request_type, status, submitted_at

**Enum Values — request_type:**
- application — initial housing application
- room_change — request to move to a different room

**Enum Values — status:**
- pending — waiting to be processed by agent
- processing — agent is currently handling this request
- completed — agent successfully resolved the request
- rejected — request could not be fulfilled (reason in rejection_reason)

**Business Rules:**
- Requests are processed in submitted_at order — first come first serve
- For room_change requests, agent validates that submitted_at is at least 3 days after the student's original allocated_at
- A friend group request is confirmed only when all named roommates have submitted matching requests listing each other
- Maximum 3 roommate requests per submission — matches maximum apartment size of 4

---

## ENUM Master List

| Enum Name | Values |
|-----------|--------|
| gender | male, female, other |
| sleep_schedule | early_bird, night_owl |
| study_habits | quiet, group |
| diet | vegetarian, non_vegetarian, vegan |
| building | A, B, C |
| room_type | private, double, triple, quad |
| maintenance_status | not_applicable, pending_escalation, escalated, work_assigned, work_in_progress, completed, rent_ready |
| allocation_status | pending, allocated, reallocated, unresolved |
| request_type | application, room_change |
| request_status | pending, processing, completed, rejected |

---

## Relationship Summary

| Relationship | Type | Description |
|-------------|------|-------------|
| students → student_preferences | 1:1 | Each student has one preference profile |
| students → allocations | 1:1 | Each student has one active allocation |
| students → requests | 1:N | A student can submit multiple requests over time |
| rooms → allocations | 1:1 | Each room has one current allocation |
| requests → allocations | 1:1 | Each allocation is triggered by one request |
| student_preferences → students (×3) | self-ref | Roommate requests point back to students table |
| requests → students (×3) | self-ref | Roommate requests in requests table point to students |
