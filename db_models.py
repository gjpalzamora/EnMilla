from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, create_engine
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()

class ClientB2B(Base):
    __tablename__ = "clients_b2b"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    nit = Column(String(50), unique=True)
    packages = relationship("Package", back_populates="client")

class Courier(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    document_id = Column(String(50), unique=True, nullable=False) # Cédula para liquidación
    packages = relationship("Package", back_populates="courier")

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True)
    tracking_number = Column(String(100), unique=True, index=True) # Guía Temu/Shein
    recipient_name = Column(String(255))
    address = Column(String(500))
    phone = Column(String(100))
    status = Column(String(50), default="RECIBIDO_SISTEMA") # EN_BODEGA, EN_REPARTO, ENTREGADO, DEVUELTO
    attempts = Column(Integer, default=0)
    client_id = Column(Integer, ForeignKey("clients_b2b.id"))
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True)
    
    client = relationship("ClientB2B", back_populates="packages")
    courier = relationship("Courier", back_populates="courier")
    logs = relationship("PackageLog", back_populates="package")

class PackageLog(Base):
    __tablename__ = "package_logs"
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey("packages.id"))
    action = Column(String(100)) # INGRESO, SALIDA_A_RUTA, FALLIDO, AUDITORIA
    observation = Column(String(500)) # Causales (Cerrado, Ausente)
    operator_id = Column(String(100)) # Quién hizo el escaneo
    timestamp = Column(DateTime, server_default=func.now())
    package = relationship("Package", back_populates="logs")
