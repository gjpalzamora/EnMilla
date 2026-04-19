from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.sql import func
import os

# Configuración Profesional
DB_URL = os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost:5432/enlaces_db")
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# --- ENTIDADES ---

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True) # Temu, Shein, etc.
    nit = Column(String(20))
    packages = relationship("Package", back_populates="client")

class Courier(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    cedula = Column(String(20), unique=True) # Clave para liquidación de pagos
    is_active = Column(Boolean, default=True)
    packages = relationship("Package", back_populates="courier")

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True)
    guide_number = Column(String(100), unique=True, index=True) # El código de barras
    
    # Datos para validación en terreno
    recipient = Column(String(200))
    address = Column(String(500))
    phone = Column(String(100))
    
    # Estados: 'PRE-CARGADO', 'EN_BODEGA', 'EN_RUTA', 'ENTREGADO', 'DEVUELTO_CLIENTE'
    status = Column(String(50), default="PRE-CARGADO")
    attempts = Column(Integer, default=0) # Contador de los 3 intentos
    
    client_id = Column(Integer, ForeignKey("clients.id"))
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=True)
    
    client = relationship("Client", back_populates="packages")
    courier = relationship("Courier", back_populates="packages")
    logs = relationship("PackageLog", back_populates="package")

class PackageLog(Base):
    """ LA HOJA DE VIDA: Aquí se guarda quién, cuándo y qué hizo con el paquete """
    __tablename__ = "package_logs"
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey("packages.id"))
    action = Column(String(100)) # 'INGRESO', 'SALIDA_MENSAJERO', 'FALLIDO', 'AUDITORIA'
    observation = Column(String(500)) # Ej: 'Dirección errada'
    operator_name = Column(String(100)) # Quién hizo el escaneo
    timestamp = Column(DateTime, server_default=func.now())
    
    package = relationship("Package", back_populates="logs")

def init_db():
    Base.metadata.create_all(bind=engine)
