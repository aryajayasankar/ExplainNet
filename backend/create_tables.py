import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from models import Base # Import the Base from our models file

# Load environment variables from .env file
load_dotenv()

# Get the database URL from the environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL environment variable not set!")

# Create a database engine
engine = create_engine(DATABASE_URL)

def main():
    print("Creating database tables...")
    # This line tells SQLAlchemy to create all tables defined in models.py
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    main()