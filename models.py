from sqlalchemy import Column, Integer, String, DateTime
from database import Base # Importación directa desde el mismo nivel
from datetime import datetime

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String, unique=True, index=True)
    recipient_name = Column(String)
    recipient_address = Column(String)
    status = Column(String, default="Recibido")
    created_at = Column(DateTime, default=datetime.utcnow)

class Courier(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
