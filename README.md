# 🏠 Housing Allocation System

> An intelligent multi-agent AI system that automates university student housing allocation — eliminating weeks of manual processing through intelligent roommate matching, compatibility scoring, and automatic reallocation.

[![CI](https://github.com/Chetanavaragantham/Housing-Allocation-System/actions/workflows/ci.yml/badge.svg)](https://github.com/Chetanavaragantham/Housing-Allocation-System/actions)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent-purple)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

---

## 📌 Problem Statement

University housing offices manually assign hundreds of students to rooms each semester using spreadsheets and manual tracking systems. This process:

- Takes **weeks** to complete per intake period
- Results in poor roommate matches leading to complaints and room change requests
- Forces students to submit separate room change requests after allocation
- Wastes housing staff time on repetitive manual coordination between RAs, RLCs, and maintenance teams

**The result:** Students wait weeks for housing, staff are overwhelmed, and the university's campus life quality suffers.

---

## ✅ Solution

An AI-powered multi-agent system that:

1. **Intakes** student applications and room change requests automatically
2. **Validates** eligibility, roommate group completeness, and request timing
3. **Allocates** students to compatible rooms using weighted compatibility scoring
4. **Prioritises** friend group placements before individual matching
5. **Reallocates** automatically when rooms fail inspection
6. **Notifies** students at every step via email
7. **Flags** unresolved cases for human review

What took weeks now takes minutes.

---

## 🏗️ System Architecture

```
Students / Staff (Browser / Mobile)
              ↓
         FastAPI (REST API · Port 8000)
              ↓
      LangGraph Multi-Agent System
       ├── Intake Agent      (Python — no LLM)
       ├── Validation Agent  (Python — no LLM)
       ├── Allocation Agent  (Gemini API — LLM reasoning)
       └── Notification Agent (Python — no LLM)
              ↓
       Agent Tools (search_rooms · score_compatibility · assign · reallocate)
              ↓
       PostgreSQL 15 (Docker · 6 Tables)
              ↓
       LangSmith (Observability · Every decision traced)
```

> **Hybrid Architecture:** Only the Allocation Agent uses an LLM — reducing API costs by ~75% compared to fully LLM-driven systems.

---

## 🤖 Agent Decision Flow

```
Queue loads (unresolved first → pending by submission date)
  ↓
Request type check
  └── Room change → 3-day buffer check
        └── Too early → HOLD + email student
  ↓
Roommate request check
  └── Has roommates → mutual confirmation check
        └── Incomplete group → HOLD + email
        └── Full group → find apartment with enough rooms
              └── No apartment → HOLD + email
              └── Found → assign group → email all
  ↓
Individual matching
  └── Search partial rooms first (existing residents)
        └── Compatibility score ≥ 0.65 → assign → email
        └── Score too low → try next room
  └── Search empty rooms
        └── Found → assign → email
        └── Not found → increment attempts
              └── Attempts < 3 → retry
              └── Attempts = 3 → UNRESOLVED → human review queue
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API | FastAPI | REST API, request validation, auto Swagger docs |
| Agent | LangGraph | Stateful multi-agent orchestration |
| LLM | Gemini API | Room allocation reasoning |
| ORM | SQLAlchemy + Alembic | Database models and migrations |
| Database | PostgreSQL 15 | Persistent data storage |
| Validation | Pydantic | Request/response schema validation |
| Auth | JWT (python-jose) | Token-based authentication |
| Observability | LangSmith | Agent decision tracing |
| Testing | pytest + pytest-cov | Unit and integration tests |
| CI/CD | GitHub Actions | Auto-run tests on every push |
| Containerisation | Docker + Docker Compose | Full stack deployment |
| Data Generation | Python + Faker | Realistic synthetic dataset |

---

## 📊 Database Schema

6 tables with full relational integrity:

```
students ──────────── student_preferences (1:1)
    │                      └── self-referential FK (roommate requests)
    ├──────────────── allocations (1:1)
    │                      └── FK → rooms
    │                      └── FK → requests
    └──────────────── requests (1:N)
                           └── FK × 3 → students (roommate requests)
                      notifications (audit trail)
```

---

## 🏢 Housing Inventory

4 buildings — 1,176 rooms total:

| Building | Floors | Room Type | Total Rooms |
|---------|--------|-----------|-------------|
| Eagle | 7 | Quad (4 beds) | 336 |
| Peacock | 5 | Private / Double / Triple | 300 |
| Dolphin | 5 | Double / Quad | 240 |
| Shark | 5 | Private / Double / Triple | 300 |

---

## 🚀 Getting Started

### Prerequisites
- Docker Desktop
- Python 3.12+
- Git

### 1. Clone the repository
```bash
git clone https://github.com/Chetanavaragantham/Housing-Allocation-System.git
cd Housing-Allocation-System
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Fill in your values
```

### 3. Start the full stack
```bash
docker compose up -d
```

### 4. Run database migrations
```bash
alembic upgrade head
```

### 5. Generate synthetic data
```bash
python data/generate_data.py
```

### 6. Access the API
```
http://localhost:8000/docs
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing
```

**Test Results:**
```
26 passed — 0 failed
65% code coverage
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|---------|-------------|
| POST | /api/v1/auth/register | Register student |
| POST | /api/v1/auth/login | Login |
| POST | /api/v1/requests/ | Submit application |
| PATCH | /api/v1/requests/{id} | Edit application |
| PATCH | /api/v1/requests/{id}/cancel | Cancel application |
| GET | /api/v1/allocations/me | View my allocation |
| GET | /api/v1/allocations/ | View all allocations (staff) |
| GET | /api/v1/allocations/unresolved | View unresolved cases |
| POST | /api/v1/agent/run | Trigger agent run |
| GET | /api/v1/agent/metrics | View allocation metrics |

Full interactive documentation at `/docs`

---

## 📈 Agent Performance (Synthetic Data Run)

```
Total students:        800
Successfully allocated:  98  (first partial run)
On hold:               107  (waiting for roommate submissions)
Unresolved:              6  (flagged for human review)
Notifications sent:    211
Average latency:      0.03s per request
```

---

## 📁 Project Structure

```
housing-allocation-system/
├── agent/                 ← LangGraph agent
│   ├── graph.py           ← Graph definition, nodes, edges
│   ├── nodes.py           ← All 8 agent node functions
│   ├── runner.py          ← Agent queue runner
│   └── state.py           ← HousingAgentState TypedDict
├── api/                   ← FastAPI routes
│   ├── auth.py
│   ├── requests_router.py
│   ├── allocations_router.py
│   └── agent_router.py
├── data/                  ← Synthetic data generation
│   └── generate_data.py
├── db/                    ← Database connection
│   └── database.py
├── docs/                  ← All project documentation
│   ├── requirements.md
│   ├── architecture_v2.html
│   ├── erd_v2.html
│   ├── api_contract.md
│   ├── agent_flow.html
│   ├── sequence_diagram.html
│   └── data_dictionary.md
├── models/                ← SQLAlchemy models + Pydantic schemas
├── tests/                 ← pytest test suite
├── alembic/               ← Database migrations
├── docker-compose.yml
├── Dockerfile
└── main.py
```

---

## 📄 Documentation

| Document | Description |
|---------|-------------|
| [Requirements](docs/requirements.md) | Functional + non-functional requirements |
| [Architecture](docs/architecture_v2.html) | Complete system architecture with all 10 agent lifecycle components |
| [ERD](docs/erd_v2.html) | Entity relationship diagram |
| [API Contract](docs/api_contract.md) | Full API specification |
| [Agent Flow](docs/agent_flow.html) | Complete agent decision flow |
| [Sequence Diagram](docs/sequence_diagram.html) | End-to-end request sequence |
| [Data Dictionary](docs/data_dictionary.md) | Every table and column documented |

---

## 🔍 Observability

Every agent decision is traced in LangSmith — input state, output state, latency, and decision path visible per run.

---

## 🗺️ Roadmap

**v2.0 planned features:**
- Room readiness inspection workflow (RA → RLC → Maintenance loop)
- Real-time email notifications via SendGrid
- Student portal UI (React)
- Multi-campus support
- Smartsheet integration for existing housing offices

---

## 👩‍💻 Author

**Chetana Varagantham**
Built as a flagship portfolio project demonstrating end-to-end AI agent engineering.

---

## 📅 Changelog

See [CHANGELOG.md](CHANGELOG.md)
