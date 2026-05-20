from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.config import DATABASE_URL
from api.models import Base

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully")

if __name__ == "__main__":
    init_db()