from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Build the database URL from environment variables
DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}"
    f":{os.getenv('POSTGRES_PASSWORD')}"
    f"@127.0.0.1:5432"
    f"/{os.getenv('POSTGRES_DB')}"
)

# Create the engine — one per application
engine = create_engine(DATABASE_URL)

# Session factory — call SessionLocal() to get a new session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class — all models will inherit from this
Base = declarative_base()


# Dependency — used later in FastAPI to get a db session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()