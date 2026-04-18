from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True)
    is_active = Column(Boolean, default=True)
    shipments = relationship("ClientShipment", back_populates="client")

class ClientShipment(Base):
    __tablename__ = "client_shipments"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    client_tracking_number = Column(String(100), unique=True)
    internal_tracking_number = Column(String(100), unique=True)
    quantity_total = Column(Integer)
    quantity_available = Column(Integer)
    status = Column(String(50), default="Recibido en Bodega")
    client = relationship("Client", back_populates="shipments")
    packages = relationship("Package", back_populates="origin_shipment")

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    internal_tracking_number = Column(String(100), unique=True)
    client_shipment_id = Column(Integer, ForeignKey("client_shipments.id"), nullable=True)
    sender_name = Column(String(255))
    recipient_name = Column(String(255))
    recipient_address = Column(Text)
    status = Column(String(50), default="Recibido")
    is_delivered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    origin_shipment = relationship("ClientShipment", back_populates="packages")
