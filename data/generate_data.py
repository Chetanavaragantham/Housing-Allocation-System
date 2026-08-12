import random
import sys
import os
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.orm import Session

# Add project root to path so we can import our models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal, engine
from models import (
    Student, StudentPreference, Room,
    Request, Allocation, Notification
)
from models.room import RoomType, MaintenanceStatus
from models.student import Gender
from models.student_preferences import SleepSchedule, StudyHabits, Diet
from models.request import RequestType, RequestStatus

# Set seed for reproducibility — same data every run
SEED = 42
random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

# Constants
TOTAL_STUDENTS = 800
RENT_READY_RATIO = 0.85

def generate_rooms(db: Session):
    print("Generating rooms...")
    rooms = []

    buildings = {
        "Eagle": {
            "floors": 7,
            "apartments_per_floor": 12,
            "room_type": RoomType.quad,
            "rooms_per_apartment": 4
        },
        "Peacock": {
            "floors": 5,
            "apartments_per_floor": 30,
            "room_types": [
                (RoomType.private, 10, 1),
                (RoomType.double,  10, 2),
                (RoomType.triple,  10, 3)
            ]
        },
        "Dolphin": {
            "floors": 5,
            "apartments_per_floor": 16,
            "room_types": [
                (RoomType.double, 8, 2),
                (RoomType.quad,   8, 4)
            ]
        },
        "Shark": {
            "floors": 5,
            "apartments_per_floor": 30,
            "room_types": [
                (RoomType.private, 10, 1),
                (RoomType.double,  10, 2),
                (RoomType.triple,  10, 3)
            ]
        }
    }

    letters = "ABCD"

    for building_name, config in buildings.items():
        floors = config["floors"]

        if building_name == "Eagle":
            for floor in range(1, floors + 1):
                for apt in range(1, config["apartments_per_floor"] + 1):
                    apt_number = f"{floor}{apt:02d}"
                    for i in range(config["rooms_per_apartment"]):
                        room_number = f"{apt_number}{letters[i]}"
                        is_rent_ready = random.random() < RENT_READY_RATIO

                        maintenance_status = MaintenanceStatus.not_applicable
                        room_issues = None

                        if not is_rent_ready:
                            status_choice = random.random()
                            if status_choice < 0.4:
                                maintenance_status = MaintenanceStatus.pending_escalation
                                room_issues = fake.sentence()
                            elif status_choice < 0.7:
                                maintenance_status = MaintenanceStatus.escalated
                                room_issues = fake.sentence()
                            elif status_choice < 0.9:
                                maintenance_status = MaintenanceStatus.work_in_progress
                                room_issues = fake.sentence()
                            else:
                                maintenance_status = MaintenanceStatus.completed
                                room_issues = "Work completed — awaiting inspection"

                        room = Room(
                            room_number=room_number,
                            building=building_name,
                            apartment_number=apt_number,
                            room_type=config["room_type"],
                            is_occupied=False,
                            is_rent_ready=is_rent_ready,
                            room_issues=room_issues,
                            maintenance_status=maintenance_status
                        )
                        rooms.append(room)

        else:
            for floor in range(1, floors + 1):
                apt_counter = 1
                for room_type, count, rooms_per_apt in config["room_types"]:
                    for apt in range(count):
                        apt_number = f"{floor}{apt_counter:02d}"
                        apt_counter += 1
                        for i in range(rooms_per_apt):
                            room_number = f"{apt_number}{letters[i]}"
                            is_rent_ready = random.random() < RENT_READY_RATIO

                            maintenance_status = MaintenanceStatus.not_applicable
                            room_issues = None

                            if not is_rent_ready:
                                status_choice = random.random()
                                if status_choice < 0.4:
                                    maintenance_status = MaintenanceStatus.pending_escalation
                                    room_issues = fake.sentence()
                                elif status_choice < 0.7:
                                    maintenance_status = MaintenanceStatus.escalated
                                    room_issues = fake.sentence()
                                elif status_choice < 0.9:
                                    maintenance_status = MaintenanceStatus.work_in_progress
                                    room_issues = fake.sentence()
                                else:
                                    maintenance_status = MaintenanceStatus.completed
                                    room_issues = "Work completed — awaiting inspection"

                            room = Room(
                                room_number=room_number,
                                building=building_name,
                                apartment_number=apt_number,
                                room_type=room_type,
                                is_occupied=False,
                                is_rent_ready=is_rent_ready,
                                room_issues=room_issues,
                                maintenance_status=maintenance_status
                            )
                            rooms.append(room)

    db.add_all(rooms)
    db.commit()
    print(f"✅ Generated {len(rooms)} rooms")
    return rooms

def generate_students(db: Session):
    print("Generating students...")
    students = []

    for i in range(1, TOTAL_STUDENTS + 1):
        first_name = fake.first_name()
        last_name  = fake.last_name()
        student_id = f"STU{i:04d}"
        email      = f"{first_name.lower()}.{last_name.lower()}{i}@university.edu"

        student = Student(
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=fake.phone_number()[:15],
            date_of_birth=fake.date_of_birth(minimum_age=17, maximum_age=25),
            gender=random.choice(list(Gender)),
            intake_date=fake.date_between(
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2026, 9, 1)
            ),
            is_allocated=False
        )
        students.append(student)

    db.add_all(students)
    db.commit()
    print(f"✅ Generated {len(students)} students")
    return students

def generate_preferences(db: Session, students: list):
    print("Generating student preferences...")
    preferences = []

    # We'll assign roommate preferences after all preferences are created
    # So first create preferences without roommate requests
    for student in students:
        preference = StudentPreference(
            student_id=student.id,
            sleep_schedule=random.choice(list(SleepSchedule)),
            noise_tolerance=random.randint(1, 5),
            cleanliness=random.randint(1, 5),
            study_habits=random.choice(list(StudyHabits)),
            diet=random.choice(list(Diet)),
            requested_roommate_1=None,
            requested_roommate_2=None,
            requested_roommate_3=None
        )
        preferences.append(preference)

    db.add_all(preferences)
    db.commit()

    # Now assign mutual roommate requests — 50% of students in friend pairs/groups
    students_needing_roommates = random.sample(students, int(TOTAL_STUDENTS * 0.5))

    # Split into pairs and groups of 3
    i = 0
    while i < len(students_needing_roommates) - 1:
        # 70% pairs, 30% groups of 3
        if random.random() < 0.7 or i + 2 >= len(students_needing_roommates):
            # Create mutual pair
            s1 = students_needing_roommates[i]
            s2 = students_needing_roommates[i + 1]

            pref1 = db.query(StudentPreference).filter_by(student_id=s1.id).first()
            pref2 = db.query(StudentPreference).filter_by(student_id=s2.id).first()

            pref1.requested_roommate_1 = s2.id
            pref2.requested_roommate_1 = s1.id
            i += 2
        else:
            # Create mutual group of 3
            s1 = students_needing_roommates[i]
            s2 = students_needing_roommates[i + 1]
            s3 = students_needing_roommates[i + 2]

            pref1 = db.query(StudentPreference).filter_by(student_id=s1.id).first()
            pref2 = db.query(StudentPreference).filter_by(student_id=s2.id).first()
            pref3 = db.query(StudentPreference).filter_by(student_id=s3.id).first()

            pref1.requested_roommate_1 = s2.id
            pref1.requested_roommate_2 = s3.id

            pref2.requested_roommate_1 = s1.id
            pref2.requested_roommate_2 = s3.id

            pref3.requested_roommate_1 = s1.id
            pref3.requested_roommate_2 = s2.id

            i += 3

    db.commit()
    print(f"✅ Generated {len(preferences)} student preferences with roommate requests")
    return preferences

def generate_requests(db: Session, students: list):
    print("Generating requests...")
    requests = []

    # Simulate start of semester — 80% applications, 20% room changes
    # 50 requests per week, we'll generate 4 weeks worth = 200 requests
    TOTAL_REQUESTS = 200

    # Split students into applicants
    applying_students = random.sample(students, TOTAL_REQUESTS)

    base_date = datetime(2026, 8, 1)  # Start of semester

    for i, student in enumerate(applying_students):
        # Determine request type
        # First 160 are applications (80%), last 40 are room changes (20%)
        if i < 160:
            request_type = RequestType.application
            # Spread submissions over 4 weeks
            days_offset = random.randint(0, 28)
        else:
            request_type = RequestType.room_change
            # Room changes happen later in semester
            days_offset = random.randint(14, 42)

        submitted_at = base_date + timedelta(days=days_offset)

        # Get student's roommate preferences
        pref = db.query(StudentPreference).filter_by(
            student_id=student.id
        ).first()

        request = Request(
            student_id=student.id,
            request_type=request_type,
            status=RequestStatus.pending,
            requested_roommate_1=pref.requested_roommate_1 if pref else None,
            requested_roommate_2=pref.requested_roommate_2 if pref else None,
            requested_roommate_3=pref.requested_roommate_3 if pref else None,
            submitted_at=submitted_at,
            processed_at=None
        )
        requests.append(request)

    db.add_all(requests)
    db.commit()
    print(f"✅ Generated {len(requests)} requests")
    return requests

def main():
    print("🏠 Housing Allocation System — Data Generation")
    print("=" * 50)

    db = SessionLocal()

    try:
        # Check if data already exists
        existing_students = db.query(Student).count()
        if existing_students > 0:
            print(f"⚠️  Database already has {existing_students} students.")
            print("Clear the database first before regenerating.")
            return

        # Generate in order — rooms first, then students, then preferences, then requests
        rooms    = generate_rooms(db)
        students = generate_students(db)
        prefs    = generate_preferences(db, students)
        requests = generate_requests(db, students)

        print("=" * 50)
        print("✅ Data generation complete!")
        print(f"   Rooms:       {len(rooms)}")
        print(f"   Students:    {len(students)}")
        print(f"   Preferences: {len(prefs)}")
        print(f"   Requests:    {len(requests)}")
        print("=" * 50)

    except Exception as e:
        print(f"❌ Error during generation: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()