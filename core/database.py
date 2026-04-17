from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Se utiliza variable de entorno para seguridad según RNF4.2.1 [cite: 187, 188]
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://usuario:password@localhost:5432/enmilla_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
