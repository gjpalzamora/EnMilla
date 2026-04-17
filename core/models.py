from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base  # Esto asume que database.py está en la misma carpeta

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True) # 
    tracking_number = Column(String(100), unique=True, nullable=False, index=True) # [cite: 56]
    sender_name = Column(String(255), index=True) # [cite: 57]
    recipient_name = Column(String(255), index=True) # [cite: 59]
    recipient_address = Column(Text, nullable=False) # [cite: 60]
    status = Column(String(50), default='Recibido', index=True) # [cite: 61]
    is_delivered = Column(Boolean, default=False) # [cite: 64]
    created_at = Column(DateTime, default=datetime.utcnow) # [cite: 62]
    
    movements = relationship("Movement", back_populates="package") # [cite: 91]

class Courier(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True, index=True) # [cite: 77]
    name = Column(String(255), nullable=False, index=True) # [cite: 78]
    license_plate = Column(String(50), unique=True, index=True) # [cite: 81]
    is_active = Column(Boolean, default=True) # [cite: 82]

class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True, index=True) # [cite: 69]
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=False) # [cite: 70]
    location = Column(String(255), nullable=False) # [cite: 72]
    description = Column(Text, nullable=False) # [cite: 73]
    movement_time = Column(DateTime, default=datetime.utcnow) # [cite: 74]
    
    package = relationship("Package", back_populates="movements") # [cite: 91]
