import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base, get_db
from main import app

# Use a separate test database
TEST_DATABASE_URL = "postgresql://housing_admin:housing123@127.0.0.1:5432/housing_test_db"

test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def setup_test_db():
    """Create all tables in test database."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db(setup_test_db):
    """Get a test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def client(setup_test_db):
    """Get a test HTTP client."""
    return TestClient(app)


@pytest.fixture
def sample_student(db):
    """Create a sample student for testing."""
    from models import Student
    from models.student import Gender

    student = Student(
        student_id  = "TEST001",
        first_name  = "Test",
        last_name   = "Student",
        email       = "test@university.edu",
        phone_number = "555-0001",
        gender      = Gender.female,
        is_allocated = False
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    yield student
    db.delete(student)
    db.commit()


@pytest.fixture
def sample_room(db):
    """Create a sample room for testing."""
    from models import Room
    from models.room import RoomType, MaintenanceStatus

    room = Room(
        room_number        = "TEST101A",
        building           = "Eagle",
        apartment_number   = "TEST101",
        room_type          = RoomType.double,
        is_occupied        = False,
        is_rent_ready      = True,
        maintenance_status = MaintenanceStatus.not_applicable
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    yield room
    db.delete(room)
    db.commit()