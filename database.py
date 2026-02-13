import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ✅ Use Render DATABASE_URL if available, otherwise use local
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://wealth_db_cj50_user:V2cShGqqlYKJ9ecIL5HJhiifJGkJtTaY@dpg-d67nhg6r433s73fajo50-a.singapore-postgres.render.com/wealth_db_cj50"
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
